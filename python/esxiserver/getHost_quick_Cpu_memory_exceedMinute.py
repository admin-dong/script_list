# !/usr/bin/env python
# -*- coding: utf-8 -*-
import decimal
from decimal import Decimal, ROUND_HALF_UP
import IPy
from binascii import a2b_hex
from pyDes import *
import ssl
import json
from pyVmomi import vmodl, vim
from pyVim import connect
import atexit
import argparse
import sys
sys.path.insert(0, '/usr/local/lib/python2.7/site-packages')
reload(sys)
sys.setdefaultencoding("utf-8")
ssl._create_default_https_context = ssl._create_unverified_context


def des_decrypt(message):
    k = des('shdevopsshdevops', ECB, padmode=PAD_PKCS5)
    try:
        result = k.decrypt(a2b_hex(message)).decode('utf8')
    except Exception:
        print('decrypt failed')
        exit(-1)
    else:
        return result


def help_parser():
    """
    Builds a standard argument parser with arguments for talking to vCenter

    -s service_host_name_or_ip
    -o optional_port_number
    -u required_user
    -p optional_password

    """
    parser = argparse.ArgumentParser(
        description='Standard Arguments for talking to vCenter or ESXi')

    parser.add_argument('-s', '--host',
                        # required=True,
                        default='192.168.1.165',
                        action='store',
                        help='vSphere service to connect to')

    parser.add_argument('-o', '--port',
                        type=int,
                        default=443,
                        action='store',
                        help='Port to connect on')

    parser.add_argument('-u', '--user',
                        default='mzflow@shmz.vc',
                        # required=True,
                        action='store',
                        help='User name to use when connecting to host')

    parser.add_argument('-p', '--password',
                        # required=True,
                        default='g%7tYP6s@E',
                        action='store',
                        help='Password to use when connecting to host')

    parser.add_argument('-n', '--netZone',
                        # required=True,
                        action='store',
                        default='mz',
                        help='Net Zone')
    return parser


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        super(DecimalEncoder, self).default(o)

def getComputeResource(Folder, computeResourceList):
    # 递归获取Folder下面的Folder
    if hasattr(Folder, 'childEntity'):
        for computeResource in Folder.childEntity:
            getComputeResource(computeResource, computeResourceList)
    else:
        computeResourceList.append(Folder)
    return computeResourceList

def get_pci_slot(obj, controlkey):
    pcislotnum = ''
    for i in obj.config.hardware.device:    
        try:
            key = i.key
        except:
            key = None
        if key and str(key) == str(controlkey):
            pcislotnum = i.slotInfo.pciSlotNumber
    return pcislotnum

def getwwnnum(wwnnum):
    res = ''
    first = wwnnum[::2]
    second = wwnnum[1::2]
    for i in range(8):
        res += first[i]
        res += second[i]
        res += ":"
    return(res[:-1])

def esxi_HBA_info(hbaobj, wwnip, snnum):
    wwnli = list()
    for i in hbaobj:
        wwndic = dict()
        if 'FibreChannelHba' in i.key:
            a = str(hex(i.portWorldWideName)).split('x')[1][:-1]
            if snnum != 'null':
                wwndic["sn"] = snnum
            wwndic["wwn"] = getwwnnum(a)
            wwndic["status"] = i.status
            wwndic["model"] = i.model
            wwndic["speed"] = i.speed
            wwndic["fc_hostIP"] = wwnip
            wwnli.append(wwndic)
    return wwnli

def esxi_net_info(netobj, netip, hostname):
    netli = list()
    for i in netobj:
        netdic = dict()
        netdic['netip'] = netip
        netdic['netname'] = i.device
        if i.linkSpeed:
            netdic['netspeed'] = str(i.linkSpeed.speedMb)
        netdic['netmac'] = i.mac
        netdic['hostname'] = hostname
        netli.append(netdic)
    return netli

def get_esxi_info(content, vcenter_host, netZone):
    '''
    Datacenter.hostFolder -> Folder
    hostFolder.childEntity -> list(Folder or ClusterComputeResource or ComputeResource)
    ClusterComputeResource.host -> list(HostSystem)
    ComputeResource.host -> list(HostSystem)
    :param content:
    :return:
    '''
    vm_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine],True)

    listres = list()
    for datacenter in content.rootFolder.childEntity:
        if hasattr(datacenter.hostFolder, 'childEntity'):
            hostFolder = datacenter.hostFolder
            computeResourceList = []
            computeResourceList = getComputeResource(hostFolder, computeResourceList)
            for obj in computeResourceList:
                for h in obj.host:
                    dic = dict()
                    dic['vchost'] = vcenter_host    
                    try:
                        sninfo = h.hardware.systemInfo.otherIdentifyingInfo
                    except:
                        sninfo = None
                    if sninfo: 
                        for sernum in sninfo:
                            if sernum.identifierType.label == 'Service tag':
                                esxissn = sernum.identifierValue
                                dic['sn'] = esxissn
                    if h.summary:
                        esxi_hardware = h.summary.hardware
                        if esxi_hardware:
                            numCpuThreads = esxi_hardware.numCpuThreads
                    try:
                        nic = h.config.network.vnic[0].spec
                        IP = nic.ip.ipAddress
                    except:
                        pass
                    vm_cpu = []
                    vm_memory = []
                    for vm in vm_view.view:
                        try:
                            if vm.summary.runtime.host.name == IP and str(vm.summary.runtime.powerState) == 'poweredOn':
                                vm_sumCpuCore = vm.config.hardware.numCoresPerSocket
                                sumCpuCore = vm.config.hardware.numCPU
                                vm_cpu.append(vm_sumCpuCore * sumCpuCore)
                                sum_cpu = int(sum(vm_cpu)) / int(numCpuThreads)
                                dic['cpu_exceedMinute'] = round((sum_cpu * 100),2)
                                vm_memorySizeMB = float(vm.config.hardware.memoryMB)/1024
                                vm_memory.append(vm_memorySizeMB)
                                sum_memory = round(float(sum(vm_memory)),2) / float(round(float(esxi_hardware.memorySize)/(1024*1024*1024),2))
                                dic['memory_exceedMinute'] = round((sum_memory * 100),2)
                        except:
                            pass
                    dic['netZone'] = netZone
                    dic['valueMethod'] = 'auto'
                    dic['revoke'] = 'False'
                    dic['dataStatus'] = 'effective'                   
                    dic['valueMethodAdd'] = vcenter_host
                    listres.append({k:v for k,v in dic.items() if v})             
    dicres = {}
    dicres['CIT_EsxiServer'] = listres
    return dicres

def makeConnect(parser):
    """
    :return:
    """
    try:
        service_instance = connect.SmartConnect(
            host=parser.host,
            port=parser.port,
            user=parser.user,
            pwd=parser.password
        )
        if not service_instance:
            print("Could not connect to the specified host using specified "
                  "username and password")
            return -1
        atexit.register(connect.Disconnect, service_instance)
        content = service_instance.RetrieveContent()
        dicresphy = get_esxi_info(content, parser.host, parser.netZone)
        dicres = dict(dicresphy)
        print (json.dumps(dicres, ensure_ascii=False,cls=DecimalEncoder))
    except vmodl.MethodFault as e:
        print(e)
        return -1
    return 0
    
if __name__ == '__main__':
    parser = help_parser()
    parser = parser.parse_args()
    content = makeConnect(parser)