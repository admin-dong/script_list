# !/usr/bin/env python
# -*- coding: utf-8 -*-
import IPy
from binascii import a2b_hex
from pyDes import *
import ssl
import json
from pyVmomi import vmodl, vim
from pyVim import connect
import atexit
import argparse
import datetime
import pandas as pd
ssl._create_default_https_context = ssl._create_unverified_context
defaultencoding = "utf-8"
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)


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

def get_all_vm_snapshots(vm,vcenter_host):
    #循环镜像树获取信息
    results = []
    try:
        rootSnapshots = vm.snapshot.rootSnapshotList
    except:
        rootSnapshots = []
    for snapshot in rootSnapshots:
        data={}
        data["vm_instanceID"] = vm.summary.config.instanceUuid
        data['snapshotName'] = snapshot.name
        data['description'] = snapshot.description
        data['createTime'] = str((snapshot.createTime + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S"))
        if snapshot.replaySupported == False:
            data['replaySupported'] = '否'
        else:
            data['replaySupported'] = '是'
        if snapshot.quiesced == False:
            data['quiesced'] = '否'
        else:
            data['quiesced'] = '是'
        data['valueMethod'] = '自动采集'
        data['dataStatus'] = 'effective'
        data['valueMethodAdd'] = vcenter_host
        results.append(data)
        results += get_child_snapshots(vm,snapshot,vcenter_host)
    return results

def get_child_snapshots(vm,snapshot,vcenter_host):
    results = []
    snapshots = snapshot.childSnapshotList
    for snapshot in snapshots:
        data={}
        data["vm_instanceID"] = vm.summary.config.instanceUuid
        data['snapshotName'] = snapshot.name
        data['description'] = snapshot.description
        data['createTime'] = str((snapshot.createTime + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S"))
        if snapshot.replaySupported == False:
            data['replaySupported'] = '否'
        else:
            data['replaySupported'] = '是'
        if snapshot.quiesced == False:
            data['quiesced'] = '否'
        else:
            data['quiesced'] = '是'
        data['valueMethod'] = '自动采集'
        data['dataStatus'] = 'effective'
        data['valueMethodAdd'] = vcenter_host
        results.append(data)
        results += get_child_snapshots(vm,snapshot,vcenter_host)
    return results

def parse_service_instance(content, vcenter_host,netZone):
    object_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine],True)
    Snapshot_list = []
    for vm in object_view.view:
        Snapshot_list.extend(get_all_vm_snapshots(vm,vcenter_host))
    Snapshot_dataframe = pd.DataFrame(Snapshot_list)
    Snapshot_sort = Snapshot_dataframe.sort_values(by=['createTime'],inplace=False,ascending=True)
    result = json.loads(Snapshot_sort.to_json(orient='records'))
    return {'CIT_VirtualHostSnapshot':result}

def makeConnect(parser):
    """
    :return:
    """
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
    dicresvm = parse_service_instance(content, parser.host, parser.netZone)
    print(json.dumps(dicresvm, ensure_ascii=False))

if __name__ == '__main__':
    parser = help_parser()
    parser = parser.parse_args()
    content = makeConnect(parser)



    