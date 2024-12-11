
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
        "project_id": project_id
    }

    Getecsurl = 'https://vpc.{projectna}.myhuaweicloud.com/v1/{projectida}/subnets'.format(
        projectna=project_name, projectida=project_id)

    res = requests.get(url=Getecsurl, headers=header, params=param)

    msg_dict = json.loads(json.dumps(res.json()))
    vpcs = msg_dict.get("subnets")
    vpcs_list = []
    network = []
    network_info = []
    for vpc in vpcs:
        tags_list = []
        item = dict()
        Network = dict()
        Network_info = dict()
        id = vpc.get("id")
        Network_info["vlan_id"] = id
        item["id"] = vpc.get("id")
        if vpc.get('neutron_network_id'):
            item["net_id"] = vpc.get('neutron_network_id')
        if vpc.get('neutron_subnet_id_v6'):
            item["ipv6_id"] = vpc.get("neutron_subnet_id_v6")
        paramaa = {
            "project_id": project_id,
            "subnet_id": id
        }
        vpctagsurl = 'https://vpc.{projectna}.myhuaweicloud.com/v2.0/{projectida}/subnets/{subnet_id}/tags'.format(
            projectna=project_name, projectida=project_id, subnet_id=id)
        vpcsubnets = requests.get(
            url=vpctagsurl, headers=header, params=paramaa)
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
        if vpc.get('name'):
            item["name"] = vpc.get("name")
        if vpc.get("cidr"):
            Network["net_cidr"] = vpc.get("cidr")
            Network_info["netinfo_cidr"] = vpc.get("cidr")
            item["cidr"] = vpc.get("cidr")  # v4
        Network["NetScopeTopic"] = "jinjiang_prod"
        Network["satellite"] = "10.230.194.156"
        Network_info["ansible"] = "10.230.194.156"
        if vpc.get("availability_zone"):
            Network_info["location"] = '{}_{}'.format(
                vpc.get("vpc_id"), vpc.get("availability_zone"))
        if vpc.get("status"):
            status = vpc.get("status")
            item["status"] = vpc.get("status")
        if status == "ACTIVE":
            Network_info["netinfo_status"] = "true"
        else:
            Network_info["netinfo_status"] = "false"
        if vpc.get("vpc_id"):
            item["vpc_id"] = vpc.get("vpc_id")  # vpcid
            vpc_id = vpc.get("vpc_id")  # vpcid
            vpcurl = 'https://vpc.{projectna}.myhuaweicloud.com/v1/{projectida}/vpcs/{vpc_id}'.format(
                projectna=project_name, projectida=project_id, vpc_id=vpc_id)
            vpcs = requests.get(url=vpcurl, headers=header, params=param)
            vpca = json.loads(json.dumps(vpcs.json()))
            if vpca.get('vpc'):
                item["vpc_name"] = vpca.get('vpc').get('name')  # vpcname
                item["vpc_enterprise_project_id"] = vpca.get('vpc').get('enterprise_project_id')  # vpcname
        if vpc.get("gateway_ip"):
            item["gateway_ip"] = vpc.get("gateway_ip")  # v4网关
            Network_info["gateway"] = vpc.get("gateway_ip")

        if str(vpc.get("dhcp_enable")):
            item["dhcp_enable"] = str(vpc.get("dhcp_enable"))
        if str(vpc.get("ipv6_enable")):
            item["ipv6_enable"] = str(vpc.get("ipv6_enable"))  # 是否创建v6
        if vpc.get("cidr_v6"):
            item["cidr_v6"] = vpc.get("cidr_v6")  # v6网段
        if vpc.get('dnsList'):
            item["dnsList"] = vpc.get('dnsList')

        vpcs_list.append(item)
        network.append(Network)
        network_info.append(Network_info)
    msg_dict = dict()
    msg_dict["CIT_HuaweicloudVPCsubnet"] = vpcs_list
   # msg_dict["CIT_NetworkPartition"] = network#
   # msg_dict["CIT_Network_info"] = network_info#
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

    print(dataStr)  # dataStr
