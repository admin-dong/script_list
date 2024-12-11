#!/usr/bin/python
# -*- coding: UTF-8 -*-
import json
import sys
import requests
from optparse import OptionParser
from pyDes import *
from binascii import a2b_hex


def des_decrypt(message):
    k = des('shdevopsshdevops', ECB, padmode=PAD_PKCS5)
    return k.decrypt(a2b_hex(message)).decode('utf8')


def get_data(domainname, username, userpasswd, projectname, projectid):
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

    param = {
        "project_id": project_id,
    }

    Getecsurl = 'https://vpc.{projectna}.myhuaweicloud.com/v1/{projectida}/publicips'.format(
        projectna=project_name, projectida=project_id)

    res = requests.get(url=Getecsurl, headers=header, params=param)
    resq = json.dumps(res.json())

    msg_dict = json.loads(resq)
    vpcs = msg_dict.get("publicips")
    vpcs_list = []
    server_name_list = []
    jtq_list = []
    for vpc in vpcs:
        item = dict()
        tags_list = []
        id = vpc.get("id")
        item["zone"] = project_name
        item["id"] = vpc.get("id")
        if vpc.get('public_ipv6_address'):
            item["public_ipv6_address"] = vpc.get('public_ipv6_address')
        paramaa = {
            "project_id": project_id,
            "publicip_id": id
        }
        vpcsubneturl = 'https://vpc.{projectna}.myhuaweicloud.com/v2.0/{projectida}/publicips/{publicip_id}/tags'.format(
            projectna=project_name, projectida=project_id, publicip_id=id)
        vpcsubnets = requests.get(
            url=vpcsubneturl, headers=header, params=paramaa)
        vpcsubnet = json.loads(json.dumps(vpcsubnets.json()))
        if vpcsubnet.get('tags'):
            for w in vpcsubnet.get('tags'):
                k = w.get('key')
                v = w.get('value')
                ta = '{}={}'.format(k, v)
                tags_list.append(ta)
            item["tags"] = tags_list
            for i in tags_list:
                if "PDT" in str(i.split('=')[0]):
                    item["product"] = i.split('=')[1]
                if "PJT" in str(i.split('=')[0]):
                    item["project"] = i.split('=')[1]
        if vpc.get("public_ip_address"):
            item["public_ip_address"] = vpc.get("public_ip_address")  # ip
        if vpc.get("status"):
            item["status"] = vpc.get("status")
        if vpc.get("type"):
            # item["type"] = vpc.get("type")
            if str(vpc.get("type")) == "5_telcom":
                item["type"] = "电信"
            if str(vpc.get("type")) == "5_union":
                item["type"] = "联通"
            if str(vpc.get("type")) == "5_bgp":
                item["type"] = "全动态BGP"
            if str(vpc.get("type")) == "5_sbgp":
                item["type"] = "静态BGP"
            if str(vpc.get("type")) == "5_elbbgp":
                item["type"] = "独享ELB专用"
        if vpc.get('bandwidth_id'):
            item["bandwidth_id"] = vpc.get('bandwidth_id')  # 实例id列表
            bandwidth_id = vpc.get('bandwidth_id')  # 实例id列表
        if vpc.get('enterprise_project_id'):
            item["enterprise_project_id"] = vpc.get('enterprise_project_id')
        param = {
            "project_id": project_id,
            "bandwidth_id": bandwidth_id
        }
        ecsurl = 'https://vpc.{projectna}.myhuaweicloud.com/v1/{projectida}/bandwidths/{bandwidth_id}'.format(
            projectna=project_name, projectida=project_id, bandwidth_id=bandwidth_id)
        ecss = requests.get(url=ecsurl, headers=header, params=param)
        ecs = json.loads(json.dumps(ecss.json()))
        if ecs.get('bandwidth'):
            # item["bandwidth_name"] = ecs.get('bandwidth').get('name')  #带宽名称
            item["charge_mode"] = ecs.get(
                'bandwidth').get('charge_mode')  # 带宽计费模式
            if str(ecs.get('bandwidth').get('charge_mode')) == "bandwidth":
                item["charge_mode"] = "按带宽计费"
            if str(ecs.get('bandwidth').get('charge_mode')) == "traffic":
                item["charge_mode"] = "按流量计费"
            if str(ecs.get('bandwidth').get('charge_mode')) == "95peak_plus":
                item["charge_mode"] = "按增强型95计费"
            item["size"] = ecs.get('bandwidth').get('size')  # 带宽大小
            item["share_type"] = ecs.get('bandwidth').get('share_type')  # 带宽类型
        if vpc.get('port_id'):
            port_id = vpc.get('port_id')
            param = {
                "project_id": project_id,
                "port_id": port_id
            }
            porturl = 'https://vpc.{projectna}.myhuaweicloud.com/v1/{projectida}/ports/{port_id}'.format(
                projectna=project_name, projectida=project_id, port_id=port_id)
            ports = requests.get(url=porturl, headers=header, params=param)
            port = json.loads(json.dumps(ports.json()))
            if port.get('port').get('instance_id'):
                item["instance_id"] = port.get('port').get('instance_id')
            else:
                if port.get('port').get('device_id'):
                    item["instance_id"] = port.get('port').get('device_id')
            if port.get('port').get('instance_type'):
                item["instance_type"] = port.get('port').get('instance_type')

        vpcs_list.append(item)
    msg_dict = dict()
    msg_dict["CIT_EIP"] = vpcs_list

    msg = json.dumps(msg_dict)
    return msg


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('--domainname', type=str,
                      dest='domainname')
    parser.add_option('--username', type=str,
                      dest='username')
    parser.add_option('--userpasswd', type=str,
                      dest='userpasswd')
    parser.add_option('--projectname', type=str,
                      dest='projectname')
    parser.add_option('--projectid', type=str, dest='projectid')

    (options, args) = parser.parse_args()
    domainname = options.domainname
    username = options.username
    userpasswd = des_decrypt(options.userpasswd)
    #userpasswd = options.userpasswd
    projectname = options.projectname
    projectid = options.projectid

    dataStr = get_data(domainname, username, userpasswd,
                       projectname, projectid)

    print(dataStr)

