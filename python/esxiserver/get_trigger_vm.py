# !/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
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
import datetime
sys.path.insert(0, '/usr/local/lib/python2.7/site-packages')
reload(sys)
sys.setdefaultencoding("utf-8")
ssl._create_default_https_context = ssl._create_unverified_context
from optparse import OptionParser


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
                        default='192.168.1.165',
                        # required=True,
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
                        default='191d3d1c736df457e216d1ad6e372226',
                        # required=True,
                        action='store',
                        help='Password to use when connecting to host')

    parser.add_argument('-n', '--netZone',
                        # required=True,
                        action='store',
                        default='mz',
                        help='Net Zone')
    parser.add_argument('-i', '--servername',
                        # required=True,
                        action='store',
                        help='hostname')
    
    return parser

def getComputeResource(Folder, computeResourceList):
    # 递归获取Folder下面的Folder
    if hasattr(Folder, 'childEntity'):
        for computeResource in Folder.childEntity:
            getComputeResource(computeResource, computeResourceList)
    else:
        computeResourceList.append(Folder)
    return computeResourceList

def get_vmFolder_item(result,folder_view):
    if 'SHMZ' not in result:
        result.append(folder_view.name)
        get_vmFolder_item(result,folder_view.parent)
    return result

def parse_service_instance(content, vcenter_host,netZone,servername):
    object_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)

    vm_list = []
    for obj in object_view.view:
        hostname = obj.guest.hostName
        if hostname == servername:
            data = {}
            vm_name = obj.name
            if vm_name:
                data['vm_name'] = vm_name.replace('%2f','/')

            folderList = []
            Folder = get_vmFolder_item(folderList,obj.parent)
            Folder.remove('vm')
            Folder.reverse()
            data['folder'] = '/'.join(Folder)
            if len(Folder) > 1:
                if Folder[1] != "主机模板":
                    data['env'] = Folder[1]
                else:
                    data['env'] = ''
                
            for k in obj.availableField:
                for v in obj.value:
                    if k.key == v.key and k.name == "owner":
                        data["owner"] = v.value
                    elif k.key == v.key and k.name == '计划回收时间': 
                        data["recoverytime"] = v.value
                    elif k.key == v.key and k.name == '项目': 
                        data["project"] = v.value
                    elif k.key == v.key and k.name == '申请人': 
                        data["applicant"] = v.value 
                    else:
                        pass
            for dns in obj.guest.ipStack:
                try:
                    data['dnsName'] = dns.dnsConfig.hostName
                except:
                    data['dnsName'] = ''
                        
            createDate = obj.config.createDate        
            CreationTime = str((createDate + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S"))
            if createDate:
                data["createtime"] = CreationTime       
                
            annotation = obj.summary.config.annotation
            if annotation:
                data['annotation'] = annotation
                            
            vm_instanceID = obj.summary.config.instanceUuid
            if vm_instanceID:
                data["vm_instanceID"] = vm_instanceID

            if str(obj.summary.runtime.powerState) == 'poweredOn':
                data['Powerstate'] = '开机'

            elif str(obj.summary.runtime.powerState) == 'poweredOff':
                data['Powerstate'] = '关机'

            uuid = ''.join(str(obj.summary.config.uuid).split('-'))
            if uuid:
                data['uuid'] = uuid
            
            if hostname:
                data['serverName'] = hostname
            
            if obj.summary.runtime.host.name:
                data['vm_Host'] = obj.summary.runtime.host.name

            memory = float(obj.config.hardware.memoryMB)
            if memory:
                data['memory'] = float(round((memory) / (1024),2))
            
            sumCpuCore = obj.config.hardware.numCPU
            if sumCpuCore:
                data['sumCpuCore'] = sumCpuCore
                
            for i in obj.config.datastoreUrl:
                data['storage_dish'] = i.name
            try:
                vm_cluster = obj.summary.runtime.host.parent.name
                data['vm_cluster'] = vm_cluster
            except:
                pass

            datastore_list = []
            for disk in obj.datastore:
                if hasattr(obj.config, 'hardware'):
                    for i in obj.config.hardware.device:
                        if isinstance(i, vim.vm.device.VirtualDisk):
                            datastore_dict = {}
                            datastore_dict['name'] = disk.summary.name
                            datastore_dict['disk_limit'] = round((int(disk.summary.freeSpace)) / 1024 / 1024 / 1024 / 1024 ,2)
                            datastore_dict['disknum'] = str(i.deviceInfo.label).replace('Hard disk','硬盘')
                            if i.backing.thinProvisioned == True:
                                datastore_dict['diskType'] = "精简置备"
                            if i.backing.thinProvisioned == False and i.backing.eagerlyScrub == None:
                                datastore_dict['diskType'] = "厚置备延迟置零"
                            if i.backing.eagerlyScrub == True:
                                datastore_dict['diskType'] = "厚置备快速置零"
                            if i.backing.diskMode == "persistent":
                                datastore_dict['diskMode'] = "从属"
                            if i.backing.diskMode == "independent_persistent":
                                datastore_dict['diskMode'] = "独立-持久"
                            if i.backing.diskMode == "independent_nonpersistent":
                                datastore_dict['diskMode'] = "独立-非持久"
                            if i.backing.sharing == "sharingNone":
                                datastore_dict['share'] = "未共享"
                            else:
                                datastore_dict['share'] = "共享"
                            datastore_dict['diskflie'] = i.backing.fileName.split("] ")[1]
                            datastore_dict['limit'] = i.storageIOAllocation.limit
                            datastore_dict['reservation'] = i.storageIOAllocation.reservation
                            if i.shares.level == "normal":
                                datastore_dict['portion'] = "正常"
                            elif i.shares.level == "high":
                                datastore_dict['portion'] = "高"
                            elif i.shares.level == "low":
                                datastore_dict['portion'] = "低"    
                            datastore_list.append(datastore_dict)
            data['obj_datastore'] = datastore_list

            network_data = []
            for device in obj.config.hardware.device:
                if hasattr(device, 'macAddress'):
                    network_dict = {}
                    network_dict['networkNums'] = device.deviceInfo.label
                    network_dict['segment'] = device.deviceInfo.summary
                    network_dict['macAddress'] = device.macAddress
                    if device.connectable.connected == True:
                        network_dict['connected'] = '已连接'
                    else:
                        network_dict['connected'] = '已断开连接'
                    if obj.guest.net:
                        for net in obj.guest.net:
                            if net.network != None:
                                if net.ipAddress == []:
                                    network_dict['IPAddress'] = ''
                                else:
                                    if device.key == net.deviceConfigId:
                                        ipAddressList = []
                                        for ip in net.ipConfig.ipAddress:
                                            if IPy.IP(ip.ipAddress).version() == 4:
                                                ipAddressList.append(ip.ipAddress)
                                        network_dict['ipAddress'] = ','.join(ipAddressList)
                    else:
                        network_dict['ipAddress'] = ''
                    network_data.append(network_dict)
            data['NA'] = network_data

            if hasattr(obj.config, 'hardware'):
                pcidic = dict()
                disksizes = 0
                for i in obj.config.hardware.device:
                    if isinstance(i, vim.vm.device.ParaVirtualSCSIController):
                        try:
                            pcidic[str(i.key)] = str(i.slotInfo.pciSlotNumber)
                        except:
                            continue
                    if isinstance(i, vim.vm.device.VirtualDisk):
                        disksizes += int(''.join(str(i.deviceInfo.summary).split()[0].strip().split(',')))

                if disksizes != 0:
                    data['VMdiskSize'] = float(round(disksizes /(1024*1024),2))
            ipList = []          
            try:
                if obj.guest.net:
                    for i in obj.guest.net:
                        if i.network == None:
                            pass
                        else:
                            data['network'] = i.network
                            for ip in i.ipConfig.ipAddress:
                                if i.network and i.ipConfig and i.ipAddress:
                                    if IPy.IP(ip.ipAddress).version() == 4:
                                        data['IPAddress'] = ip.ipAddress
                                else:
                                    pass
                        for ip in i.ipConfig.ipAddress:
                            if IPy.IP(ip.ipAddress).version() == 4:
                                ipList.append(str(ip.ipAddress))
                    if ipList != []:
                        data['ipList'] = ipList
                else:
                    pass
            except:
                pass
            Lwtype = {
                "linuxGuest":"Linux",
                "windowsGuest":"Windows"
            }
            if obj.guest.guestFamily != None:
                data['osType'] = Lwtype.get(obj.guest.guestFamily)
            if obj.summary.guest.guestFullName != None:
                data['osVersion'] = obj.summary.guest.guestFullName
            else:
                if obj.summary.config.guestFullName != None:
                    data['osVersion'] = obj.summary.config.guestFullName
            if obj.guest.toolsStatus == "toolsNotInstalled":
                data['vmToolsVersion'] = "未运行,未安装"
            elif obj.guest.toolsStatus  == "toolsNotRunning":
                if obj.guest.toolsVersionStatus2 == "guestToolsCurrent" or obj.guest.toolsVersionStatus2 == "guestToolsSupportedNew":
                    data['vmToolsVersion'] = '未运行,版本: {} (当前版本)'.format(obj.guest.toolsVersion)
                elif obj.guest.toolsVersionStatus2 == "guestToolsUnmanaged":
                    data['vmToolsVersion'] = '未运行,版本: {} (客户机托管)'.format(obj.guest.toolsVersion)
                elif obj.guest.toolsVersionStatus2 == "guestToolsSupportedOld":
                    data['vmToolsVersion'] = '未运行,版本: {} (可升级)'.format(obj.guest.toolsVersion)
            elif obj.guest.toolsStatus == "toolsOk" or obj.guest.toolsStatus == "toolsOld":
                if obj.guest.toolsVersionStatus2 == "guestToolsCurrent" or obj.guest.toolsVersionStatus2 == "guestToolsSupportedNew":
                    data['vmToolsVersion'] = '正在运行,版本: {} (当前版本)'.format(obj.guest.toolsVersion)
                elif obj.guest.toolsVersionStatus2 == "guestToolsUnmanaged":
                    data['vmToolsVersion'] = '正在运行,版本: {} (客户机托管)'.format(obj.guest.toolsVersion)
                elif obj.guest.toolsVersionStatus2 == "guestToolsSupportedOld":
                    data['vmToolsVersion'] = '正在运行,版本: {} (可升级)'.format(obj.guest.toolsVersion)
            data['recovery'] = 'False'
            # data['netZone'] = netZone
            data['businessStatus'] = 'file'
            data['area'] = '九州中心'
            data['valueMethod'] = '自动采集'
            data['dataStatus'] = 'effective'
            data['valueMethodAdd'] = vcenter_host
            vm_list.append(data)
    dicres = {}
    dicres['CIT_VirtualHost'] = vm_list
    return dicres


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
            #pwd=parser.password,
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
        dicresvm = parse_service_instance(content, parser.host, parser.netZone, parser.servername)
        dicres = dict(dicresvm)#, **dicresphy)
        print(json.dumps(dicres, ensure_ascii=False))
    except vmodl.MethodFault as e:
        #print(json.dumps({'ERROR': e}))
        return -1
    return 0

if __name__ == '__main__':
    parser = help_parser()
    parser = parser.parse_args()
    content = makeConnect(parser)