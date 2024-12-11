
# !/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
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
from datetime import timedelta
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
                        action='store',
                        help='vSphere service to connect to')

    parser.add_argument('-o', '--port',
                        type=int,
                        default=443,
                        action='store',
                        help='Port to connect on')

    parser.add_argument('-u', '--user',
                        # required=True,
                        action='store',
                        help='User name to use when connecting to host')

    parser.add_argument('-p', '--password',
                        # required=True,
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


def get_esxi_info(content, vcenter_host, netZone):
    '''
    Datacenter.hostFolder -> Folder
    hostFolder.childEntity -> list(Folder or ClusterComputeResource or ComputeResource)
    ClusterComputeResource.host -> list(HostSystem)
    ComputeResource.host -> list(HostSystem)
    :param content:
    :return:
    '''
    listres = list()
    wwnli = list()
    netli = list()
    for datacenter in content.rootFolder.childEntity:
        if hasattr(datacenter.hostFolder, 'childEntity'):
            hostFolder = datacenter.hostFolder
            computeResourceList = []
            computeResourceList = getComputeResource(
                hostFolder, computeResourceList)
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
                    
                    if h.datastore:
                        allcapacity = []
                        freecapacity = []
                        for ds in h.datastore:
                            allcapacity.append(float(round(float(ds.summary.capacity)/(1024.0*1024*1024),0)))
                            freecapacity.append(float(round(float(ds.summary.freeSpace)/(1024.0*1024*1024),0)))
                        dic['total_capacity'] = sum(allcapacity)
                        dic['free_capacity'] = sum(freecapacity)
                        dic['use_capacity'] = sum(allcapacity) - sum(freecapacity)
                    
                    try:
                        nic = h.config.network.vnic[0].spec
                        phynetcard = h.config.network.pnic
                        vendor = h.hardware.systemInfo.vendor
                        dic['IP'] = nic.ip.ipAddress
                        wwnVec = h.config.storageDevice.hostBusAdapter
                        if dic.get('sn'):
                            wwnum = esxi_HBA_info(
                                wwnVec, nic.ip.ipAddress, dic['sn'])
                        else:
                            wwnum = esxi_HBA_info(wwnVec, nic.ip.ipAddress, 'null')
                        dic['hbanum'] = len(wwnum)
                        for i in wwnum:
                            i.update({'valueMethodAdd':vcenter_host})
                            i.update({'dataStatus':'efficient'})
                            i.update({'valueMethod':'auto'})
                            wwnli.append(i)
                    except:
                        pass

                    if h.summary:
                        dic['manageIP'] = h.summary.managementServerIp
                        esxi_hardware = h.summary.hardware
                        if esxi_hardware:
                            dic['Memory'] = float(round(float(esxi_hardware.memorySize)/(1024*1024*1024),2))
                            dic['memory_use'] = round((float(h.summary.quickStats.overallMemoryUsage))/1024.0,2)
                            dic['memory_usable'] = round(float(dic.get('Memory')) - float(dic.get('memory_use')),2)
                            dic['cpucorenum'] = esxi_hardware.numCpuCores
                            dic['cpunum'] = esxi_hardware.numCpuPkgs
                            dic['serverModel'] = esxi_hardware.model
                            dic['serverVender'] = esxi_hardware.vendor
                            dic['CPUModel'] = esxi_hardware.cpuModel
                            dic['uuid'] = esxi_hardware.uuid
                            dic['numCpuThreads'] = esxi_hardware.numCpuThreads
                        esxi_config = h.summary.config
                        if esxi_config:
                            netres = esxi_net_info(phynetcard, nic.ip.ipAddress, esxi_config.name)
                            for i in netres:
                                i.update({'valueMethodAdd':vcenter_host})
                                i.update({'dataStatus':'efficient'})
                                i.update({'valueMethod':'auto'})
                                netli.append(i)
                            dic['OperateSystem'] = esxi_config.product.name.split()[1].strip()
                            dic['osty'] = esxi_config.product.fullName
                            dic['kernelversion'] = esxi_config.product.version
                            dic['Hostname'] = esxi_config.name
                    dic['cpu_sum'] = round(float(h.systemResources.config.cpuAllocation.limit)/1024.0,1)
                    dic['cpu_use'] = round((float(h.summary.quickStats.overallCpuUsage))/1024.0,2)
                    dic['cpu_usable'] = round(float(dic.get('cpu_sum')) - float(dic.get('cpu_use')),2)       
                    dic['Cluster'] = obj.name
                    dic['netZone'] = netZone
                    dic['valueMethod'] = 'auto'
                    dic['revoke'] = 'False'
                    dic['dataStatus'] = 'effective'
                    dic['devicecategories'] = "服务器"
                    dic['dataStatus'] = "effective"
                    dic['powerState'] = h.summary.runtime.powerState
                    if h.summary.runtime.powerState == "poweredOn":
                        dic['powerState'] = "up"
                    if h.summary.runtime.powerState == "poweredOff":
                        dic['powerState'] = "Offline"
                    if h.summary.runtime.powerState == "standBy":
                        dic['powerState'] = "Maintain"                    
                    dic['valueMethodAdd'] = vcenter_host
                    dic['MethodAdd'] = vcenter_host
                    listres.append({k:v for k,v in dic.items() if v})
                    # maps[dic['Host']] = dic['Cluster']s
                    # except:
                    #     pass
    dicres = {}
    # dicres['CIT_physicalDevice'] = listres
    dicres['CIT_EsxiServer'] = listres
    # dicres['CIT_Fcport'] = wwnli
    # dicres['CIT_ethinfo'] = netli
    #print(len(content.rootFolder.childEntity))
    return dicres


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



def makeConnect(parser):
    """
    :return:
    """
    try:
        # context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        # context.verify_mode = ssl.CERT_NONE
        service_instance = connect.SmartConnect(
            host=parser.host,
            port=parser.port,
            user=parser.user,
            #pwd=parser.password
            pwd=des_decrypt(parser.password)
            # sslContext=context
        )
        if not service_instance:
            print("Could not connect to the specified host using specified "
                  "username and password")
            return -1
        atexit.register(connect.Disconnect, service_instance)
        content = service_instance.RetrieveContent()
        # ## Do the actual parsing of data ## #
        # dicresvm = parse_service_instance(content, parser.host, parser.netZone)
        dicresphy = get_esxi_info(content, parser.host, parser.netZone)
        # dicresvmreport = VMreport(content, parser.host)
        dicres = dict(dicresphy)
        # dicres = dict(dicres, **dicresvmreport)
        print (json.dumps(dicres, ensure_ascii=False,cls=DecimalEncoder))
    except vmodl.MethodFault as e:
        print(e)
        return -1
    return 0

if __name__ == '__main__':
    parser = help_parser()
    parser = parser.parse_args()
    content = makeConnect(parser)



# ##---
# - hosts: all
#   gather_facts: no
#   vars:
#     timestamp: "{{ uuid }}"
#   tasks:
#     - name: mkdir
#       file:
#         path: /tmp/cmdb_tmp/{{timestamp}}
#         state: directory
#     - name: copy files in current path
#       copy: src=. dest=/tmp/cmdb_tmp/{{timestamp}}
#     - name: execution
#       command: "python /tmp/cmdb_tmp/{{timestamp}}/vhost.py --host {{host}} --user {{user}} --password {{password}} --netZone {{netZone}}"
#     - name: remove files in tmp
#       command: rm -rf /tmp/cmdb_tmp/{{timestamp}}