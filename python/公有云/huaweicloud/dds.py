
#!/usr/bin/python
# -*- coding: UTF-8 -*-

from binascii import a2b_hex
from pyDes import *
from optparse import OptionParser
import json
import sys
import requests
import time
import math
reload(sys)
sys.setdefaultencoding('utf-8')


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
        "limit": "1",
    }
    security_group_rules = 'https://dds.{projectna}.myhuaweicloud.com/v3/{projectida}/instances'.format(
        projectna=project_name, projectida=project_id)
    res = requests.get(url=security_group_rules, headers=header, params=param)
    msg_dict = json.loads(json.dumps(res.json()))
    total_count = msg_dict.get('total_count')
    param = {
        "project_id": project_id,
        "region": project_id
    }
    modelurl = 'https://dds.{projectna}.myhuaweicloud.com/v3/{projectida}/flavors?region={projectna}'.format(
        projectna=project_name, projectida=project_id)
    models = requests.get(url=modelurl, headers=header)
    model = json.loads(json.dumps(models.json()))
    vpcs_list = []
    DDSgroup_list = []
    DDSnode_list = []

    for i in range(0, total_count, 100):
        param = {
            "project_id": project_id,
            "limit": "100",
            "offset": i,
        }
        security_group_rules = 'https://dds.{projectna}.myhuaweicloud.com/v3/{projectida}/instances'.format(
            projectna=project_name, projectida=project_id)
        res = requests.get(url=security_group_rules,
                           headers=header, params=param)
        msg_dictt = json.loads(json.dumps(res.json()))
        vpcs = msg_dictt.get("instances")

        for vpc in vpcs:
            pp = dict()
            item = dict()
            nodes_list = []
            vlomes = []
            sizes = []
            useds = []
            nodes_ip_list = []
            tags_list = []
            total = 0
            total1 = 0
            id = vpc.get("id")  #
            item["id"] = vpc.get("id")
            paramaa = {
                "project_id": project_id,
                "instance_id": id
            }
            vpcsubneturl = 'https://dds.{projectna}.myhuaweicloud.com/v3/{projectida}/instances/{instance_id}/tags'.format(
                projectna=project_name, projectida=project_id, instance_id=id)
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
                # if tags_list != []:
                for i in tags_list:
                    if "PDT" in str(i.split('=')[0]):
                        item["product"] = i.split('=')[1]
                    if "PJT" in str(i.split('=')[0]):
                        item["project"] = i.split('=')[1]
            item["account"] = "rwuser"  # 管理员账户名
            item["region"] = vpc.get('region')
            item["name"] = vpc.get('name')
            # item["mode"] = vpc.get('mode')
            if str(vpc.get('mode')) == "Sharding":
                item["mode"] = "集群"
            if str(vpc.get('mode')) == "ReplicaSet":
                item["mode"] = "副本集"
            if str(vpc.get('mode')) == "Single":
                item["mode"] = "单节点"
            item["datastoreType"] = '{} {}'.format(vpc.get('datastore').get(
                'type'), vpc.get('datastore').get('version'))  # 数据库版本
            if vpc.get('enterprise_project_id'):
                item["enterprise_project_id"] = vpc.get(
                    'enterprise_project_id')
            if vpc.get('vpc_id'):
                item["vpc_id"] = vpc.get('vpc_id')
            if vpc.get('subnet_id'):
                item["subnet_id"] = vpc.get('subnet_id')
            if vpc.get('port'):
                item["port"] = vpc.get('port')
            if vpc.get('pay_mode'):
                if str(vpc.get('pay_mode')) == "0":
                    item["pay_mode"] = "按需"
                if str(vpc.get('pay_mode')) == "1":
                    item["pay_mode"] = "包年包月"
                if str(vpc.get('pay_mode')) == "2":
                    item["pay_mode"] = "竞价实例计费"
                # item["pay_mode"] = vpc.get('pay_mode')
            if vpc.get('created'):
                item["created"] = vpc.get('created')
            if vpc.get('status'):
                item["status"] = vpc.get('status')
            if vpc.get('groups') != []:
                for o in vpc.get('groups'):
                    gitem = dict()
                    gitem["id"] = vpc.get("id")
                    if o.get('nodes') != []:
                        item["zone"] = list(
                            set([j.get('availability_zone') for j in o.get('nodes')]))
                        zone_list = []
                        zone = list(set([j.get('availability_zone')
                                         for j in o.get('nodes')]))  # 可用区
                        for i in zone:
                            if i == "cn-east-3a" or i == "cn-east-2a" or i == "cn-south-1a":
                                a = "可用区1"
                                zone_list.append(a)
                            if i == "cn-east-3b" or i == "cn-south-2b" or i == "cn-east-2b":
                                a = "可用区2"
                                zone_list.append(a)
                            if i == "cn-east-3c" or i == "cn-east-2c" or i == "cn-south-1c":
                                a = "可用区3"
                                zone_list.append(a)
                            if i == "cn-east-2d":
                                a = "可用区4"
                                zone_list.append(a)
                            if i == "cn-south-1e":
                                a = "可用区5"
                                zone_list.append(a)
                            if i == "cn-south-1f":
                                a = "可用区6"
                                zone_list.append(a)
                        item["zonecn"] = zone_list  # 可用区
                        if 'arm' in [j.get('spec_code') for j in o.get('nodes')]:
                            item["cpu_type"] = "arm"
                        else:
                            item["cpu_type"] = "X86"
                        for k in o.get('nodes'):
                            nitem = dict()
                            nodes_list.append(k)
                            nodes_ip_list = []
                            nitem["id"] = id
                            if k.get('id'):
                                nitem["node_id"] = k.get('id')
                            if k.get('name'):
                                nitem["node_name"] = k.get('name')
                            if k.get('status'):
                                nitem["node_status"] = k.get('status')
                            if k.get('role'):
                                nitem["node_role"] = k.get('role')
                            if k.get('private_ip'):
                                nitem["node_private_ip"] = k.get('private_ip')
                            if k.get('public_ip'):
                                nitem["node_public_ip"] = k.get('public_ip')
                            if k.get('availability_zone'):
                                nitem["node_availability_zone"] = k.get(
                                    'availability_zone')
                            if k.get('spec_code'):
                                node_spec_code = k.get('spec_code')
                                num = node_spec_code[12:14]
                                for l in model.get('flavors'):
                                    if node_spec_code == l.get('spec_code'):
                                        nitem["spec"] = '{}|{}vCPUS|{}GB'.format(
                                            num, l.get('vcpus'), l.get('ram'))
                            DDSnode_list.append(nitem)
                    if o.get('id'):
                        gitem["group_id"] = o.get('id')
                        if o.get('type'):
                            gitem["group_type"] = o.get('type')

                        if o.get('volume'):
                            gitem["group_volume"] = [o.get('volume')]
                        aaa_list = []

                        if o.get('name'):
                            gitem["group_name"] = o.get('name')
                        if o.get('status'):
                            gitem["group_status"] = o.get('status')
                        DDSgroup_list.append(gitem)
                    group_type = o.get('type')
                    if group_type == 'shard':
                        si_ze = float(o.get('volume').get('size'))
                        us_ed = float(o.get('volume').get('used'))
                        sizes.append(si_ze)
                        useds.append(us_ed)
                    elif group_type == 'replica':
                        si_ze = float(o.get('volume').get('size'))
                        us_ed = float(o.get('volume').get('used'))
                        sizes.append(si_ze)
                        useds.append(us_ed)

                    if o.get('type'):
                        gtype = o.get('type')
                        if gtype == "mongos" or gtype == "replica" or gtype == "sigle":
                            no_ip = [j.get('private_ip')
                                     for j in o.get('nodes')]  # node_ip列表
                            for h in no_ip:
                                aaa = 'mongos{}:8635'.format(h)
                                nodes_ip_list.append(aaa)
                ccc = ','.join(nodes_ip_list)
                item["ha_address"] = 'mongodb://rwuser:****@{}/test?authSource=admin'.format(
                    ccc)

            size = sum(sizes)
            used = sum(useds)
            pp["size"] = str(("%.0f" % size))
            pp["used"] = str(("%.2f" % used))
            pp["type"] = "超高IO"
            vlomes.append(pp)
            item["group_size"] = vlomes

            vpcs_list.append(item)

    msg_dict = dict()
    msg_dict["CIT_DDS"] = vpcs_list
    msg_dict["CIT_DDSGroups"] = DDSgroup_list
    msg_dict["CIT_DDSNodes"] = DDSnode_list
    msg = json.dumps(msg_dict, ensure_ascii=False)

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
    # userpasswd = options.userpasswd
    projectname = options.projectname
    projectid = options.projectid

    dataStr = get_data(domainname, username, userpasswd,
                       projectname, projectid)

    print(dataStr)  # dataStr
