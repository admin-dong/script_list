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


def getComputeResource(Folder, computeResourceList):
    # 递归获取Folder下面的Folder
    if hasattr(Folder, 'childEntity'):
        for computeResource in Folder.childEntity:
            getComputeResource(computeResource, computeResourceList)
    else:
        computeResourceList.append(Folder)
    return computeResourceList


def parse_service_instance(content, vcenter_host,netZone):
    object_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine],True)

    vm_list = []
    for obj in object_view.view:
        data = {}

        vm_name = obj.name
        if vm_name:
            data['vm_name'] = vm_name.replace('%2f','/')
                           
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

        if obj.guest.hostName:
            data['serverName'] = obj.guest.hostName
        
        try: 
            data['vm_Host'] = obj.summary.runtime.host.name
        except:
            data['vm_Host'] = ''

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
                    for ip in i.ipConfig.ipAddress:
                        if IPy.IP(ip.ipAddress).version() == 4:
                            ipList.append(str(ip.ipAddress))

                data['ipList'] = ipList
            else:
                pass
        except:
            pass

        for dns in obj.guest.ipStack:
            try:
                data['dnsName'] = dns.dnsConfig.hostName
            except:
                data['dnsName'] = ''
				

        data['recovery'] = 'False'
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
        dicresvm = parse_service_instance(content, parser.host, parser.netZone)
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