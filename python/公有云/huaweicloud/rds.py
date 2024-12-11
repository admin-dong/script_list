#!/usr/bin/python
# -*- coding: UTF-8 -*-
import commands
import json
import sys
import requests
import time
from optparse import OptionParser
from pyDes import *
from binascii import a2b_hex
reload(sys)
sys.setdefaultencoding('utf8')


def des_decrypt(message):
    k = des('shdevopsshdevops', ECB, padmode=PAD_PKCS5)
    return k.decrypt(a2b_hex(message)).decode('utf8')


def geteps_data(domainname, username, userpasswd):
    domain_name = domainname
    user_name = username
    user_passwd = userpasswd
    project_name = 'cn-north-4'
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
                        "password": user_passwd,  # IAM用户密码

                    }
                }
            },
            "scope": {
                "domin": {
                    "name": domain_name              #
                }
            }
        }
    }
    header = {
        "User-Agent": "test",
        "Content-Type": "application/json"
    }
    tokenurl = 'https://iam.myhuaweicloud.com/v3/auth/tokens'

    req = requests.post(url=tokenurl, data=json.dumps(reqdata), headers=header)
    token = req.headers["X-Subject-Token"]
    header["X-Auth-Token"] = token
    return header


def get_data(domainname, username, userpasswd, projectname, projectid, instances_id):
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
    epsheader = geteps_data(domainname, username, userpasswd)
    req = requests.post(url=tokenurl, data=json.dumps(reqdata), headers=header)
    token = req.headers["X-Subject-Token"]
    header["X-Auth-Token"] = token
    Getepsurl = 'https://eps.myhuaweicloud.com/v1.0/enterprise-projects?limit=1000'
    ree = requests.get(url=Getepsurl, headers=epsheader)
    epss = json.loads(json.dumps(ree.json()))
    eps = epss.get("enterprise_projects")

    ##################
    param = {
        "project_id": project_id,
        "id": instances_id
        # "limit":100
    }
    Getecsurl = 'https://rds.{projectna}.myhuaweicloud.com/v3/{projectida}/instances?id={i}'.format(
        projectna=project_name, projectida=project_id, i=instances_id)
    instances_list = []
    res = requests.get(url=Getecsurl, headers=header, params=param)
    msg_dict = json.loads(json.dumps(res.json()))
    instances = msg_dict.get("instances")
    for instance in instances:
        itema = dict()
        tags_list = []
        itema["id"] = instance.get("id")
        itema["region"] = project_name
        #itema["status"] = instance.get("status")
        if str(instance.get("status")) == "Delete":
            itema["status"] = "delete"
        else:
            itema["status"] = instance.get("status")
        itema["name"] = instance.get("name")
        if instance.get('tags'):
            for w in instance.get('tags'):
                k = w.get('key')
                v = w.get('value')
                ta = '{}={}'.format(k, v)
                tags_list.append(ta)
            itema["tags"] = tags_list
            for i in tags_list:
                if "PDT" in str(i.split('=')[0]):
                    itema["product"] = i.split('=')[1]
                if "PJT" in str(i.split('=')[0]):
                    itema["project"] = i.split('=')[1]
        if [i.get('availability_zone') for i in instance.get('nodes')]:
            zone_list = []
            zone = [i.get('availability_zone')
                    for i in instance.get('nodes')]  # 可用区
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
            item["zone"] = zone_list  # 可用区
        rds_type = instance.get('datastore').get('type')
        if instance.get('flavor_ref'):
            flavor_ref = instance.get('flavor_ref')
            cpu = instance.get('cpu')
            itema["cpu"] = instance.get('cpu')
            itema["memory"] = instance.get('mem')
            ram = instance.get('mem')
            itema["spec_code"] = '{} | {} vCPUs | {} GB'.format(
                flavor_ref, cpu, ram)
        itema["engine_version"] = '{} {}'.format(instance.get('datastore').get(
            'type'), instance.get('datastore').get('version'))  # 引擎版本
        mysql_type = instance.get('datastore').get('type')
        if mysql_type == 'MySQL':
            itema["admin"] = "root"
        elif mysql_type == 'SQLServer':
            itema["admin"] = "rdsuser"
        elif mysql_type == 'PostgreSQL':
            itema["admin"] = "root"
        itema["type"] = instance.get("type")  # 实例类型
        type = instance.get("type")
        itema["enterprise_project_id"] = instance.get(
            "enterprise_project_id")  # 企业项目
        enterprise_project_id = instance.get("enterprise_project_id")
        for i in eps:
            if i.get('id') == str(enterprise_project_id):
                itema["enterprise_project_name"] = i.get("name")  # 企业项目
        if type == "Ha":  # sync_type
            itema["sync_type"] = instance.get('ha').get('replication_mode')
        itema["vpc_id"] = instance.get("vpc_id")  # vpcid
        vpc_id = instance.get("vpc_id")  # vpcid
        param = {
            "project_id": project_id,
            "vpc_id": vpc_id
        }
        vpcurl = 'https://vpc.{projectna}.myhuaweicloud.com/v1/{projectida}/vpcs/{vpc_id}'.format(
            projectna=project_name, projectida=project_id, vpc_id=vpc_id)
        vpcs = requests.get(url=vpcurl, headers=header, params=param)
        vpca = json.loads(json.dumps(vpcs.json()))
        itema["vpc_name"] = vpca.get('vpc').get('name')  # vpcname
        itema["subnet_id"] = instance.get("subnet_id")  # 子网id
        subnet_id = instance.get("subnet_id")  # 子网id
        param = {
            "project_id": project_id,
            "subnet_id": subnet_id
        }
        subneturl = 'https://vpc.{projectna}.myhuaweicloud.com/v1/{projectida}/subnets/{subnet_id}'.format(
            projectna=project_name, projectida=project_id, subnet_id=subnet_id)
        subnets = requests.get(url=subneturl, headers=header, params=param)
        subnet = json.loads(json.dumps(subnets.json()))
        itema["subnet_name"] = subnet.get(
            'subnet').get('name')  # subnet_name
        if instance.get("private_dns_names"):
            itema["private_dns_names"] = instance.get(
                "private_dns_names")  # 内网域名列表
        if instance.get("private_ips"):
            itema["private_ips"] = instance.get("private_ips")  # 内网IP地址列表
        if instance.get("port"):
            itema["port"] = instance.get("port")
        if instance.get("created"):
            itema["created"] = instance.get("created")
        if instance.get("charge_info").get('charge_mode'):
            itema["order_type"] = instance.get(
                "charge_info").get('charge_mode')  # 计费模式
        if instance.get("volume").get('type'):
            itema["storage_type"] = instance.get(
                "volume").get('type')  # 存储类型
        if instance.get("volume") == "MySQL":
            itema["user"] = "root"
        elif instance.get('volume') == "SQLServer":
            itema["user"] = "rdsuser"
        else:
            itema["user"] = "root"
        if instance.get("volume").get('size'):
            itema["storage_size"] = instance.get(
                "volume").get('size')  # 存储大小
        if instance.get('mem') == "512":
            itema["max_connections"] = "100000"
        elif instance.get('mem') == "384":
            itema["max_connections"] = "80000"
        elif instance.get('mem') == "256":
            itema["max_connections"] = "60000"
        elif instance.get('mem') == "128":
            itema["max_connections"] = "30000"
        elif instance.get('mem') == "64":
            itema["max_connections"] = "18000"
        elif instance.get('mem') == "32":
            itema["max_connections"] = "10000"
        elif instance.get('mem') == "16":
            itema["max_connections"] = "5000"
        elif instance.get('mem') == "8":
            itema["max_connections"] = "2500"
        elif instance.get('mem') == "4":
            itema["max_connections"] = "1500"
        elif instance.get('mem') == "2":
            itema["max_connections"] = "800"
        instances_list.append(itema)
    msg_dict = dict()
    msg_dict["CIT_HuaweicloudRDS"] = instances_list
    msg = json.dumps(msg_dict, ensure_ascii=False)
    return msg


def newdata(instances_id):
    tokens = commands.getoutput(
        '''curl -i -k  -s -H "Cookie:DefaultLanguage=zh-CN; sessionid=404e36b7d3604d55ab0d5b4567d81023; token==OL6NJIB+EtSO3E8UOtbizXdrQ8BLm/mDJDhqos1z+RsEqk4bWnEAPpx2Y1GlDwWf9Fflhak81H1rJ7XHF9Qi9Z+SaclCHrUiu3MJvr19/oFoQNbpWAMoJP0ZM9oa9r1h0wQm/3+dbUxttlWLngkFuw==" -H "Content-Type:application/json"  -X POST -d '{"username":"admin","password":"admin888"}' http://10.230.211.219:9069/login/direct |grep { ''')
    tmm = tokens.replace("\"success\":true,", "")
    tokens = json.loads(tmm).get('param')
    token = '"Authorization:{}"'.format(tokens)
    serverid = '"id":"{}"'.format(instances_id)
    cmdss = '''curl -i -k  -H "Cookie:DefaultLanguage=zh-CN; sessionid=404e36b7d3604d55ab0d5b4567d81023; token==OL6NJIB+EtSO3E8UOtbizXdrQ8BLm/mDJDhqos1z+RsEqk4bWnEAPpx2Y1GlDwWf9Fflhak81H1rJ7XHF9Qi9Z+SaclCHrUiu3MJvr19/oFoQNbpWAMoJP0ZM9oa9r1h0wQm/3+dbUxttlWLngkFuw==" -H "Content-Type:application/json" -H "Authorization:" -X POST -d '{"data":{"id":,"type":"rds"},"mid":"0a28938b650b426695df5564fb5a1bb7","moduleName":"新增","name":"新增"}' http://10.230.211.219:9069/storage/direct'''
    cmd = cmdss.replace("\"Authorization:\"", token)
    cmda = cmd.replace("\"id\":", serverid)
    acmds = commands.getoutput(cmda)


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('--domainname', type=str,dest='domainname')
    parser.add_option('--username', type=str,dest='username')
    parser.add_option('--userpasswd', type=str,dest='userpasswd')
    parser.add_option('--projectname', type=str,dest='projectname')
    parser.add_option('--projectid', type=str, dest='projectid')
    parser.add_option('--instances_id', type=str,dest='instances_id')

    (options, args) = parser.parse_args()
    domainname = options.domainname
    username = options.username
    #userpasswd = options.userpasswd
    userpasswd = des_decrypt(options.userpasswd)
    projectname = options.projectname
    projectid = options.projectid
    instances_id = options.instances_id

    dataStr = get_data(domainname, username, userpasswd,
                       projectname, projectid, instances_id)
    if dataStr:
        print(dataStr)
        newdata(instances_id)

