# !/usr/bin/env python
# -*- coding: utf-8 -*-
from binascii import a2b_hex
from pyDes import *
import ssl
import json
from pyVmomi import vmodl, vim
from pyVim import connect
import atexit
import argparse
import sys
import re
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
                        default='g%7tYP6s@E',
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




def get_esxi_info(content, vcenter_host):
    '''
    Datacenter.hostFolder -> Folder
    hostFolder.childEntity -> list(Folder or ClusterComputeResource or ComputeResource)
    ClusterComputeResource.host -> list(HostSystem)
    ComputeResource.host -> list(HostSystem)
    :param content:
    :return:
    '''
    lunli = list()
    for datacenter in content.rootFolder.childEntity:
        if hasattr(datacenter.hostFolder, 'childEntity'):
            hostFolder = datacenter.hostFolder
            computeResourceList = []
            computeResourceList = getComputeResource(
                hostFolder, computeResourceList)
            for obj in computeResourceList:
                for h in obj.datastore:
                    lun_dic = {}
                    lun_dic['lunName'] = h.summary.name
                    lun_dic['overdue'] = "true"
                    lun_dic['fileSystemType'] = h.info.vmfs.type
                    lun_dic['version'] = h.info.vmfs.version
                    lun_dic['diskType'] = {'true': 'ssd', 'false': 'Hdd'}.get(
                        str(h.info.vmfs.ssd).lower())
                    lun_dic['capacity'] = int(
                        round(int(h.summary.capacity) / (1024 * 1024 * 1024), 0))
                    lun_dic['freespace'] = int(
                        round(int(h.summary.freeSpace) / (1024 * 1024 * 1024), 0))
                    lun_dic['usedCapacity'] = lun_dic['capacity'] - \
                        lun_dic['freespace']
                    lun_dic['store_status'] = str(h.summary.accessible).lower()
                    lun_dic['dataStatus'] = '有效'
                    try:
                        for host in h.host:
                            lun_dic['physicalMachineList'] = host.key.name
                    except:
                        pass
                    if lun_dic not in lunli:
                        lunli.append(lun_dic)

    dicres = {}
    dicres['CIT_VirtualPool'] = lunli
#    print(len(content.rootFolder.childEntity))
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
            pwd=parser.password,
            #pwd=des_decrypt(parser.password),
            # sslContext=context
        )
        if not service_instance:
            print("Could not connect to the specified host using specified "
                  "username and password")
            return -1
        atexit.register(connect.Disconnect, service_instance)
        content = service_instance.RetrieveContent()
        # ## Do the actual parsing of data ## #
        dicresphy = get_esxi_info(content, parser.host)
        # dicresvmreport = VMreport(content, parser.host)
        dicres = dict(dicresphy)
        # dicres = dict(dicres, **dicresvmreport)
        print(json.dumps(dicres, ensure_ascii=False))
    except vmodl.MethodFault as e:
        print(json.dumps({'ERROR': e}))
        return -1
    return 0


if __name__ == '__main__':
    parser = help_parser()
    parser = parser.parse_args()
    content = makeConnect(parser)
