#!/usr/bin/python
# -*- coding: UTF-8 -*-
import json
import sys
import requests
from optparse import OptionParser
import time
import datetime
from pyDes import *
from binascii import a2b_hex
reload(sys)
sys.setdefaultencoding('utf-8')


def des_decrypt(message):
    k = des('shdevopsshdevops', ECB, padmode=PAD_PKCS5)
    return k.decrypt(a2b_hex(message)).decode('utf8')


def get_data(domainname, username, userpasswd, projectname, projectid, elbtype):
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
    elbid_list = []
    header["X-Auth-Token"] = token
    param = {
        "project_id": project_id,
        "limit": "2000",
    }

    if elbtype == "shared":
        loadbalancers = 'https://elb.{projectna}.myhuaweicloud.com/v2/{projectida}/elb/loadbalancers'.format(
            projectna=project_name, projectida=project_id)
        res = requests.get(url=loadbalancers, headers=header, params=param)
        msg_dict = json.loads(json.dumps(res.json()))
        ser_id = []
        elbids = [i.get('id') for i in msg_dict.get('loadbalancers')]
        num_id = elbids[-1]
        elbid_list.append(elbids)
        ser_id.append(num_id)
        num = 1
        vpcs_list = []
        while num < 10000:
            num_id = ser_id[num-1]
            header["X-Auth-Token"] = token
            paramu = {
                "project_id": project_id,
                "limit": "2000",
                "marker": num_id
            }
            testurl = 'https://elb.{projectna}.myhuaweicloud.com/v2/{projectida}/elb/loadbalancers'.format(
                projectna=project_name, projectida=project_id)
            reas = requests.get(url=testurl, headers=header, params=paramu)
            msgdict = json.loads(json.dumps(reas.json()))
            elbidss = [i.get('id') for i in msgdict.get('loadbalancers')]

            if elbidss != []:
                bbb = elbidss[-1]
                elbid_list.append(elbidss)
                ser_id.append(bbb)
                num += 1
            else:
                break
        for u in elbid_list:
            for i in u:
                item = dict()
                jtq_list = []
                param = {
                    "project_id": project_id,
                    "loadbalancer_id": i
                }
                loadbalancera = 'https://elb.{projectna}.myhuaweicloud.com/v2/{projectida}/elb/loadbalancers/{loadbalancer_id}'.format(
                    projectna=project_name, projectida=project_id, loadbalancer_id=i)
                elbs = requests.get(url=loadbalancera,
                                    headers=header, params=param)
                elb = json.loads(json.dumps(elbs.json()))
                if elb.get('loadbalancer').get('name'):
                    item["name"] = elb.get('loadbalancer').get('name')
                item["id"] = elb.get('loadbalancer').get('id')
                item["region"] = project_name
                # if elb.get('loadbalancer').get('vip_port_id'):
                vip_port_id = elb.get('loadbalancer').get('vip_port_id')
                if elb.get('loadbalancer').get('vip_address'):
                    item["vip_address"] = elb.get(
                        'loadbalancer').get('vip_address')  # 内网ip
                if elb.get('loadbalancer').get('provisioning_status'):
                    item["status"] = elb.get('loadbalancer').get(
                        'provisioning_status')
                paramss = {
                    "project_id": project_id,
                    "loadbalancer_id": i
                }

                porturl = 'https://elb.{projectna}.myhuaweicloud.com/v1/{projectida}/publicips?port_id={vip_port_id}'.format(
                    projectna=project_name, projectida=project_id, vip_port_id=vip_port_id)
                portss = requests.get(url=porturl, headers=header)
                portt = json.loads(json.dumps(portss.json()))
                if portt.get('publicips'):
                    public_ip_addressa = [i.get('public_ip_address')
                                          for i in portt.get('publicips')]
                    if public_ip_addressa:
                        item["public_ip_address"] = public_ip_addressa[0]  # 公网IP
                # if elb.get('loadbalancer').get('vip_subnet_id'):
                vip_subnetid = elb.get('loadbalancer').get(
                    'vip_subnet_id')  # 负载均衡器所在子网的ID
                if elb.get('loadbalancer').get('tags') != []:
                    item["tags"] = elb.get('loadbalancer').get('tags')
                    for i in elb.get('loadbalancer').get('tags'):
                        if "PDT" in str(i.split('=')[0]):
                            item["product"] = i.split('=')[1]
                        if "PJT" in str(i.split('=')[0]):
                            item["project"] = i.split('=')[1]

                paramu = {
                    "project_id": project_id,
                }
                vpcsubneturl = 'https://vpc.{projectna}.myhuaweicloud.com/v1/{projectida}/subnets'.format(
                    projectna=project_name, projectida=project_id)
                vpcsubnets = requests.get(
                    url=vpcsubneturl, headers=header, params=paramu)
                vpcsubnet = json.loads(json.dumps(vpcsubnets.json()))
                if vpcsubnet.get('subnets'):
                    subnet_ids = vpcsubnet.get('subnets')
                    for j in subnet_ids:
                        if vip_subnetid == j.get('neutron_subnet_id'):
                            item["vip_subnet_id"] = j.get('neutron_network_id')
                            item["subnet_name"] = j.get('name')
                            item["vpc_id"] = j.get('vpc_id')
                            item["vpc_name"] = j.get('vpc_id')
                if elb.get('loadbalancer').get('created_at'):
                    item["created_at"] = elb.get(
                        'loadbalancer').get('created_at')
                if elb.get('loadbalancer').get('enterprise_project_id'):
                    item["enterprise_project_id"] = elb.get(
                        'loadbalancer').get('enterprise_project_id')
                item["net_type"] = "共享型"
                if elb.get('loadbalancer').get('listeners'):
                    listeners = elb.get('loadbalancer').get('listeners')
                    listeners_id = [i.get('id') for i in listeners]

                    for i in listeners_id:
                        paraml = {
                            "project_id": project_id,
                            "listener_id": i
                        }
                        aaa = 'https://elb.{projectna}.myhuaweicloud.com/v2/{projectida}/elb/listeners/{listener_id}'.format(
                            projectna=project_name, projectida=project_id, listener_id=i)
                        bbb = requests.get(
                            url=aaa, headers=header, params=paraml)
                        ccc = json.loads(json.dumps(bbb.json()))
                        listeners_name = ccc.get('listener').get('name')
                        jtq_list.append(listeners_name)
                    item["listener_name"] = jtq_list

                vpcs_list.append(item)
        msg_dict = dict()
        msg_dict["CIT_LoadBalancer"] = vpcs_list
        msg = json.dumps(msg_dict, ensure_ascii=False)

        return msg
    elif elbtype == "exclusive":
        loadbalancers = 'https://elb.{projectna}.myhuaweicloud.com/v3/{projectida}/elb/loadbalancers'.format(
            projectna=project_name, projectida=project_id)
        res = requests.get(url=loadbalancers, headers=header, params=param)
        msg_dict = json.loads(json.dumps(res.json()))
        ser_id = []
        elbids = [i.get('id') for i in msg_dict.get('loadbalancers')]
        num_id = elbids[-1]
        elbid_list.append(elbids)
        ser_id.append(num_id)
        num = 1
        vpcs_list = []
        while num < 10000:
            num_id = ser_id[num-1]
            header["X-Auth-Token"] = token
            paramu = {
                "project_id": project_id,
                "limit": "2000",
                "marker": num_id
            }
            testurl = 'https://elb.{projectna}.myhuaweicloud.com/v3/{projectida}/elb/loadbalancers'.format(
                projectna=project_name, projectida=project_id)
            reas = requests.get(url=testurl, headers=header, params=paramu)
            msgdict = json.loads(json.dumps(reas.json()))
            elbidss = [i.get('id') for i in msgdict.get('loadbalancers')]

            if elbidss != []:
                bbb = elbidss[-1]
                elbid_list.append(elbidss)
                ser_id.append(bbb)
                num += 1
            else:
                break
        for u in elbid_list:
            for i in u:
                tags_list = []
                item = dict()
                jtq_list = []
                subid_list = []
                netid_liss = []
                flavorid_list = []
                param = {
                    "project_id": project_id,
                    "loadbalancer_id": i
                }
                loadbalancera = 'https://elb.{projectna}.myhuaweicloud.com/v3/{projectida}/elb/loadbalancers/{loadbalancer_id}'.format(
                    projectna=project_name, projectida=project_id, loadbalancer_id=i)
                elbs = requests.get(url=loadbalancera,
                                    headers=header, params=param)
                elb = json.loads(json.dumps(elbs.json()))
                if elb.get('loadbalancer').get('name'):
                    item["name"] = elb.get('loadbalancer').get('name')
                item["id"] = elb.get('loadbalancer').get('id')
                if elb.get('loadbalancer').get('l4_flavor_id'):
                    flavoridl4 = str(
                        elb.get('loadbalancer').get('l4_flavor_id'))
                    flavorid_list.append(flavoridl4)
                if elb.get('loadbalancer').get('l7_flavor_id'):
                    flavoridl7 = str(
                        elb.get('loadbalancer').get('l7_flavor_id'))
                    flavorid_list.append(flavoridl7)
                if elb.get('loadbalancer').get('l4_scale_flavor_id'):
                    flavoridsl4 = str(elb.get('loadbalancer').get(
                        'l4_scale_flavor_id'))
                    flavorid_list.append(flavoridsl4)
                if elb.get('loadbalancer').get('l7_scale_flavor_id'):
                    flavoridsl7 = str(elb.get('loadbalancer').get(
                        'l7_scale_flavor_id'))
                    flavorid_list.append(flavoridsl7)
                if flavorid_list != []:
                    flavor_id = flavorid_list[0]
                    flavorurl = 'https://elb.{projectna}.myhuaweicloud.com/v3/{projectida}/elb/flavors/{flavorid}'.format(
                        projectna=project_name, projectida=project_id, flavorid=flavor_id)
                    flavor = requests.get(
                        url=flavorurl, headers=header, params=param)
                    flavor_dict = json.loads(json.dumps(flavor.json()))
                    flavor_type = str(flavor_dict.get('flavor').get('type'))

                    if flavor_type == "L4":
                        elbspec_type_list = []
                        elb_type = "网络型(TCP/UDP)"
                        connection = str(flavor_dict.get(
                            'flavor').get('info').get('connection'))
                        cps = str(flavor_dict.get(
                            'flavor').get('info').get('cps'))
                        if cps == "10000" or connection == "500000":
                            elbspec_type = "小型 I"
                        elif cps == "20000" or connection == "1000000":
                            elbspec_type = "小型 II"
                        elif cps == "40000" or connection == "2000000":
                            elbspec_type = "中型 I"
                        elif cps == "80000" or connection == "4000000":
                            elbspec_type = "中型 II"
                        elif cps == "200000" or connection == "10000000":
                            elbspec_type = "大型 I"
                        elif cps == "400000" or connection == "20000000":
                            elbspec_type = "大型 II"
                        item["elb_spec"] = '{} | {}'.format(
                            elb_type, elbspec_type)
                        elb_spec = '{} | {}'.format(elb_type, elbspec_type)

                    elif flavor_type == "L7":
                        elb_type = "应用型(HTTP/HTTPS)"
                        connection = str(flavor_dict.get(
                            'flavor').get('info').get('connection'))
                        cps = str(flavor_dict.get(
                            'flavor').get('info').get('cps'))
                        if cps == "2000" or connection == "200000":
                            elbspec_type = "小型 I"
                        elif cps == "4000" or connection == "400000":
                            elbspec_type = "小型 II"
                        elif cps == "8000" or connection == "800000":
                            elbspec_type = "中型 I"
                        elif cps == "20000" or connection == "2000000":
                            elbspec_type = "中型 II"
                        elif cps == "40000" or connection == "4000000":
                            elbspec_type = "大型 I"
                        elif cps == "80000" or connection == "8000000":
                            elbspec_type = "大型 II"
                        item["elb_spec"] = '{} | {}'.format(
                            elb_type, elbspec_type)
                item["region"] = project_name
                # if elb.get('loadbalancer').get('vip_port_id'):
                vip_portid = elb.get('loadbalancer').get('vip_port_id')
                if elb.get('loadbalancer').get('vip_address'):
                    item["vip_address"] = elb.get(
                        'loadbalancer').get('vip_address')  # 内网ip
                if elb.get('loadbalancer').get('publicips') != []:
                    publicips = [i.get('publicip_address')
                                 for i in elb.get('loadbalancer').get('publicips')]
                    item["public_ip_address"] = publicips[0]
                if elb.get('loadbalancer').get('provisioning_status'):
                    item["status"] = elb.get('loadbalancer').get(
                        'provisioning_status')
                if elb.get('loadbalancer').get('elb_virsubnet_ids'):
                    netid_list = elb.get('loadbalancer').get(
                        'elb_virsubnet_ids')  # 负载均衡器所在子网的ID
                    for m in netid_list:
                        ntid = str(m)
                    netid_liss.append(ntid)

                if elb.get('loadbalancer').get('vip_subnet_cidr_id'):
                    subid_list.append(str(elb.get('loadbalancer').get(
                        'vip_subnet_cidr_id')))  # 负载均衡器所在子网的ID
                if netid_liss != []:
                    vip_net_id = netid_liss[0]
                    paramu = {
                        "project_id": project_id,
                    }
                    vpcsubneturl = 'https://vpc.{projectna}.myhuaweicloud.com/v1/{projectida}/subnets'.format(
                        projectna=project_name, projectida=project_id)
                    vpcsubnets = requests.get(
                        url=vpcsubneturl, headers=header, params=paramu)
                    vpcsubnet = json.loads(json.dumps(vpcsubnets.json()))
                    if vpcsubnet.get('subnets'):
                        subnet_ids = vpcsubnet.get('subnets')
                        for j in subnet_ids:
                            if vip_net_id == j.get('neutron_network_id'):
                                item["vip_subnet_id"] = j.get(
                                    'neutron_network_id')
                                item["subnet_name"] = j.get('name')
                                item["vpc_id"] = j.get('vpc_id')
                                item["vpc_name"] = j.get('vpc_id')

                if subid_list != []:
                    vip_subnet_id = str(subid_list[0])
                    paramu = {
                        "project_id": project_id,
                    }
                    vpcsubneturl = 'https://vpc.{projectna}.myhuaweicloud.com/v1/{projectida}/subnets'.format(
                        projectna=project_name, projectida=project_id)
                    vpcsubnets = requests.get(
                        url=vpcsubneturl, headers=header, params=paramu)
                    vpcsubnet = json.loads(json.dumps(vpcsubnets.json()))
                    if vpcsubnet.get('subnets'):
                        subnet_ids = vpcsubnet.get('subnets')
                        for j in subnet_ids:
                            if vip_subnet_id == j.get('neutron_subnet_id'):
                                item["vip_subnet_id"] = j.get(
                                    'neutron_network_id')
                                item["subnet_name"] = j.get('name')
                                item["vpc_id"] = j.get('vpc_id')
                                item["vpc_name"] = j.get('vpc_id')

                if elb.get('loadbalancer').get('tags') != []:
                    for w in elb.get('loadbalancer').get('tags'):
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
                if elb.get('loadbalancer').get('created_at'):
                    item["created_at"] = elb.get(
                        'loadbalancer').get('created_at')
                if elb.get('loadbalancer').get('enterprise_project_id'):
                    item["enterprise_project_id"] = elb.get(
                        'loadbalancer').get('enterprise_project_id')
                if str(elb.get('loadbalancer').get('guaranteed')):
                    type = str(
                        elb.get('loadbalancer').get('guaranteed'))
                    if type == 'True':
                        item["net_type"] = "独享型"
                    else:
                        item["net_type"] = "共享型"
                    paramss = {
                        "project_id": project_id,
                        "loadbalancer_id": i
                    }
                    porturl = 'https://elb.{projectna}.myhuaweicloud.com/v2/{projectida}/publicips?port_id={vip_portida}'.format(
                        projectna=project_name, projectida=project_id, vip_portida=vip_portid)
                    portss = requests.get(url=porturl, headers=header)
                    portt = json.loads(json.dumps(portss.json()))
                    if portt.get('publicips'):
                        public_ip_addressa = [i.get('public_ip_address')
                                              for i in portt.get('publicips')]
                        if public_ip_addressa:
                            # 公网IP
                            item["public_ip_address"] = public_ip_addressa[0]
                if elb.get('loadbalancer').get('listeners'):
                    listeners = elb.get(
                        'loadbalancer').get('listeners')
                    listeners_id = [i.get('id') for i in listeners]
                    for i in listeners_id:
                        paraml = {
                            "project_id": project_id,
                            "listener_id": i
                        }
                        aaa = 'https://elb.{projectna}.myhuaweicloud.com/v2/{projectida}/elb/listeners/{listener_id}'.format(
                            projectna=project_name, projectida=project_id, listener_id=i)
                        bbb = requests.get(
                            url=aaa, headers=header, params=paraml)
                        ccc = json.loads(json.dumps(bbb.json()))
                        listeners_name = ccc.get(
                            'listener').get('name')
                        jtq_list.append(listeners_name)
                    item["listener_name"] = jtq_list

                vpcs_list.append(item)
        msg_dict = dict()
        msg_dict["CIT_LoadBalancer"] = vpcs_list
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
    parser.add_option('--elbtype', type=str,
                      dest='elbtype', default='exclusive')

    (options, args) = parser.parse_args()
    domainname = options.domainname
    username = options.username
    #userpasswd = options.userpasswd
    userpasswd = des_decrypt(options.userpasswd)
    projectname = options.projectname
    projectid = options.projectid
    elbtype = options.elbtype

    dataStr = get_data(domainname, username, userpasswd,
                       projectname, projectid, elbtype)

    print(dataStr)
