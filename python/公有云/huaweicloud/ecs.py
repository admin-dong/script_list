
#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys
import uuid
import requests
import time
import base64
import json
import time
import commands
from pyDes import *
import copy
from Crypto.Cipher import AES
from base64 import b64decode, b64encode
from optparse import OptionParser
from binascii import a2b_hex
defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)


def des_decrypt(message):
    k = des('shdevopsshdevops', ECB, padmode=PAD_PKCS5)
    return k.decrypt(a2b_hex(message)).decode('utf8')


def get_data(domainname, username, userpasswd, projectname, projectid, server_id):
    domain_name = domainname
    user_name = username
    user_passwd = userpasswd
    project_name = projectname
    project_id = projectid
    reqdata = {
        "auth": {
            "identity": {
                "methods": [
                    "password"
                ],
                "password": {
                    "user": {
                        "domain": {
                            "name": domain_name  # IAM用户所属账号名
                        },
                        "name": user_name,  # IAM用户名
                        "password": user_passwd  # IAM用户密码
                    }
                }
            },
            "scope": {
                "project": {
                    "name": project_name  # 项目名称
                }
            }
        }
    }
    header = {
        "User-Agent": "test",
        "Content-Type": "application/json"
    }
    tokenurl = 'https://iam.{projectna}.myhuaweicloud.com/v3/auth/tokens'.format(
        projectna=project_name)
    req = requests.post(url=tokenurl, data=json.dumps(reqdata), headers=header)
    token = req.headers["X-Subject-Token"]
    header["X-Auth-Token"] = token

    ########################
    param = {
        "project_id": project_id,
        "server_id": server_id
    }
    Getecsurl = 'https://ecs.{projectna}.myhuaweicloud.com/v1/{projectida}/cloudservers/{server_id}'.format(
        projectna=project_name, projectida=project_id, server_id=server_id)
    res = requests.get(url=Getecsurl, headers=header, params=param)
    resq = json.loads(json.dumps(res.json()))
    vpcs = resq.get("server")
    item = dict()
    ipadd = dict()
    host = dict()
    volme = dict()
    volme_list = []
    vpcs_lists = []
    host_list = []
    ip_list = []
    sub_list = []
    item["id"] = vpcs.get("id")
    id = vpcs.get("id")
    # uuids = id.split('-')
    # host["uuid"] = ''.join(uuids)
    item["name"] = vpcs.get("name")
    if vpcs.get("OS-EXT-AZ:availability_zone"):
        item["zone"] = vpcs.get("OS-EXT-AZ:availability_zone")  # 可用区
    if vpcs.get("metadata").get("vpc_id"):
        item["vpc_id"] = vpcs.get("metadata").get("vpc_id")
    vpc_id = vpcs.get("metadata").get("vpc_id")  # 虚拟私有云id
    paramm = {
        "project_id": project_id,
        "vpc_id": vpc_id
    }
    Getecsurl = 'https://vpc.{projectna}.myhuaweicloud.com/v1/{projectida}/vpcs/{vpc_id}'.format(
        projectna=project_name, projectida=project_id, vpc_id=vpc_id)
    vpc_name = requests.get(url=Getecsurl, headers=header, params=paramm)
    vpcn = json.loads(json.dumps(vpc_name.json()))
    item["vpcname"] = vpcn.get('vpc').get('name')  # vpc名称
    # host["vpcname"] = vpcn.get('vpc').get('name')  # vpc名称
    if vpcs.get("key_name"):
        item["key_name"] = vpcs.get("key_name")  # 云服务器使用的密钥对名称
    item["charging_mode"] = vpcs.get(
        "metadata").get("charging_mode")  # 计费类型
    if vpcs.get('tags'):
        item["tags"] = vpcs.get('tags')
        for i in vpcs.get('tags'):
            if "PDT" in str(i.split('=')[0]):
                item["product"] = i.split('=')[1]
            if "PJT" in str(i.split('=')[0]):
                item["project"] = i.split('=')[1]
    flavor_id = vpcs.get('flavor').get('id')  # 规格id
    flavor_vcpus = vpcs.get('flavor').get('vcpus')  # 规格cpu
    item["cpu"] = flavor_vcpus
    # host["host_cpu"] = flavor_vcpus
    # .encode('utf-8') #规格内存
    flavorram = int(vpcs.get('flavor').get('ram'))
    flavor_ram = (flavorram/1024)
    item["memory"] = flavor_ram
    # host["host_ram"] = flavorram
    item["specific"] = '{flavorid} | {flavorvcpus}vCPUs | {flavorram}GB'.format(
        flavorid=flavor_id, flavorvcpus=flavor_vcpus, flavorram=flavor_ram)
    addresses_data = vpcs.get("addresses")  # 网络属性信息
    addresses = list(addresses_data.values())[0]  # 整理后网络属性信息
    addressesa = list(addresses_data.values())[0][0]  # 整理后网络属性信息
    for i in addresses:
        # IP地址类型 fixed为私有IP、floating为浮动IP
        if i.get("OS-EXT-IPS:type") == "fixed":
            ipadd["IpAddress"] = i.get("addr")
        else:
            ipadd["IpAddress"] = addresses.get("addr")
    if vpcs.get("created"):
        item["created_time"] = vpcs.get("created")  # 云服务器创建时间
    if vpcs.get('status'):
        stat = str(vpcs.get('status'))
    if stat == "BUILD" or stat == "REBOOT" or stat == "HARD_REBOOT" or stat == "HARD_REBOOT" or stat == "REBUILD" or stat == "MIGRATING" or stat == "RESIZE" or stat == "ACTIVE" or stat == "REVERT_RESIZE" or stat == "VERIFY_RESIZE":
        item["status"] = "ACTIVE"
    elif stat == "SHUTOFF":
        item["status"] = "SHUTOFF"
    elif stat == "ERROR":
        item["status"] = "ERROR"
    elif stat == "DELETED":
        item["status"] = "delete"
    if vpcs.get("os-extended-volumes:volumes_attached"):
        os_extended_volumes = vpcs.get(
            "os-extended-volumes:volumes_attached")
        size_list = []
        disk_list = []
        for os_extended_volume in os_extended_volumes:
            os_extended_volume_id = os_extended_volume.get(
                "id")  # volume_id
            volume_id = os_extended_volume_id
            param = {
                "project_id": project_id,
                "volume_id": os_extended_volume_id
            }
            diskurl = 'https://evs.{projectna}.myhuaweicloud.com/v2/{projectida}/cloudvolumes/{volume_id}'.format(
                projectna=project_name, projectida=project_id, volume_id=volume_id)
            disks = requests.get(url=diskurl, headers=header, params=param)
            disk = json.loads(json.dumps(disks.json()))
            disk_dict = dict()
            if disk.get("volume").get('bootable') == "true":  # 判断系统盘或数据盘
                item["sys_disk_size"] = disk.get("volume").get('size')
                # host["sys_disk_size"] = disk.get("volume").get('size')
                # disk_dict["otherDiskSize"] = disk.get("volume").get('size')
                if disk.get("volume").get("volume_type") == "SSD":
                    item["s_IOPSa"] = "超高IO"
                    # host["s_IOPSa"] = "超高IO"
                    # disk_dict["otherDiskType"] = "超高IO"
                elif disk.get("volume").get("volume_type") == "ESSD":
                    item["s_IOPSa"] = "极速型SSD"
                    # host["s_IOPSa"] = "极速型SSD"
                    # disk_dict["otherDiskType"] = "极速型SSD"
                elif disk.get("volume").get("volume_type") == "SAS":
                    item["s_IOPSa"] = "高IO"
                    # host["s_IOPSa"] = "高IO"
                    # disk_dict["otherDiskType"] = "高IO"
                elif disk.get("volume").get("volume_type") == "GPSSD":
                    item["s_IOPSa"] = "通用型SSD"
                    # disk_dict["otherDiskType"] = "通用型SSD"
                    # host["s_IOPSa"] = "通用型SSD"
                else:
                    item["s_IOPSa"] = "普通IO"
                    # disk_dict["otherDiskType"] = "普通IO"
                    # host["s_IOPSa"] = "普通IO"
                # disk_list.append(disk_dict)
            else:
                item["data_disk_size"] = disk.get("volume").get('size')
                # host["data_disk_size"] = disk.get("volume").get('size')
                # disk_dict["otherDiskSize"] = disk.get("volume").get('size')
                if disk.get("volume").get("volume_type") == "SSD":
                    item["d_IOPSa"] = "超高IO"
                    # host["d_IOPSa"] = "超高IO"
                    # disk_dict["otherDiskType"] = "超高IO"
                elif disk.get("volume").get("volume_type") == "ESSD":
                    item["d_IOPSa"] = "极速型SSD"
                    # host["d_IOPSa"] = "极速型SSD"
                    # disk_dict["otherDiskType"] = "极速型SSD"
                elif disk.get("volume").get("volume_type") == "SAS":
                    item["d_IOPSa"] = "高IO"
                    # host["d_IOPSa"] = "高IO"
                    # disk_dict["otherDiskType"] = "高IO"
                elif disk.get("volume").get("volume_type") == "GPSSD":
                    item["d_IOPSa"] = "通用型SSD"
                    # host["d_IOPSa"] = "通用型SSD"
                    # disk_dict["otherDiskType"] = "通用型SSD"
                else:
                    item["d_IOPSa"] = "普通IO"
                    # host["d_IOPSa"] = "普通IO"
                    # disk_dict["otherDiskType"] = "普通IO"
            if disk.get("volume").get('size'):
                size_list.append(disk.get("volume").get('size'))
            disk_list.append(disk_dict)
        total = 0
        for ele in range(0, len(size_list)):
            total = total + size_list[ele]
        # host["size_sum"] = total
        # host["diskInfo"] = disk_list
    if vpcs.get("metadata").get('image_name'):
        item["image_name"] = vpcs.get("metadata").get('image_name')  # 镜像
    item["region"] = project_name   #
    ipadd["region"] = project_name
    item["enterprise_project_id"] = vpcs.get('enterprise_project_id')  # 企业项目ID
    # vpcs_lists.append(item)
    return item
    # ip_list.append(ipadd)
    # host_list.append(host)
    # msg_dict = dict()
    # # msg_dict["CIT_Ipaddress"] = ip_list
    # msg_dict["CIT_HuaweicloudECS"] = vpcs_lists
    # # msg_dict["CIT_ecs2host"] = host_list
    # msg = json.dumps(msg_dict, ensure_ascii=False)
    # return msg


def newdata(server_id):
    tokens = commands.getoutput(
        '''curl -i -k  -s -H "Cookie:DefaultLanguage=zh-CN; sessionid=404e36b7d3604d55ab0d5b4567d81023; token==OL6NJIB+EtSO3E8UOtbizXdrQ8BLm/mDJDhqos1z+RsEqk4bWnEAPpx2Y1GlDwWf9Fflhak81H1rJ7XHF9Qi9Z+SaclCHrUiu3MJvr19/oFoQNbpWAMoJP0ZM9oa9r1h0wQm/3+dbUxttlWLngkFuw==" -H "Content-Type:application/json"  -X POST -d '{"username":"admin","password":"admin888"}' http://10.230.211.219:9069/login/direct |grep { ''')
    tmm = tokens.replace("\"success\":true,", "")
    tokens = json.loads(tmm).get('param')
    token = '"Authorization:{}"'.format(tokens)
    serverids = '"id":"{}"'.format(server_id)
    cmdss = '''curl -i -k  -H "Cookie:DefaultLanguage=zh-CN; sessionid=404e36b7d3604d55ab0d5b4567d81023; token==OL6NJIB+EtSO3E8UOtbizXdrQ8BLm/mDJDhqos1z+RsEqk4bWnEAPpx2Y1GlDwWf9Fflhak81H1rJ7XHF9Qi9Z+SaclCHrUiu3MJvr19/oFoQNbpWAMoJP0ZM9oa9r1h0wQm/3+dbUxttlWLngkFuw==" -H "Content-Type:application/json" -H "Authorization:" -X POST -d '{"data":{"id":,"type":"ecs"},"mid":"be5550185e7848af9b68642d9b23494d","moduleName":"新增","name":"新增"}' http://10.230.211.219:9069/storage/direct'''
    cmd = cmdss.replace("\"Authorization:\"", token)
    cmda = cmd.replace("\"id\":", serverids)
    acmds = commands.getoutput(cmda)


if __name__ == "__main__":
    parser = OptionParser()
    # parser.add_option('--host', type=str, dest='host',
    #                   default='10.236.196.2')
    # parser.add_option('--accessKey', type=str, default='enUuHyxk2rgtx9En')
    # parser.add_option('--secretKey', type=str, default='tPcbk6nZi0nmqOVB')
    parser.add_option('--domainname', type=str,dest='domainname')
    parser.add_option('--username', type=str,dest='username')
    parser.add_option('--userpasswd', type=str,dest='userpasswd')
    parser.add_option('--projectname', type=str,dest='projectname')
    parser.add_option('--projectid', type=str, dest='projectid')
    parser.add_option('--server_id', type=str, dest='server_id')
    (options, args) = parser.parse_args()
    #host = options.host
    # accessKey = options.accessKey
    # secretKey = options.secretKey
    domainname = options.domainname
    username = options.username
    userpasswd = des_decrypt(options.userpasswd)
    #userpasswd = options.userpasswd
    projectname = options.projectname
    projectid = options.projectid
    server_id = options.server_id
    dataaa = list()
    nnn = dict()
    dataStr = get_data(domainname, username, userpasswd,
                       projectname, projectid, server_id)
    if dataStr:
        dataaa.append(dataStr)
        nnn["CIT_HuaweicloudECS"] = dataaa
        print json.dumps(nnn, ensure_ascii=False)
        newdata(server_id)
