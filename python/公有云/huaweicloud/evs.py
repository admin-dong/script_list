#!/usr/bin/python
# -*- coding: UTF-8 -*-
import json
import sys
import requests
from optparse import OptionParser
from pyDes import *
from binascii import a2b_hex
reload(sys)
sys.setdefaultencoding('utf8')


def des_decrypt(message):
    k = des('shdevopsshqz', ECB, padmode=PAD_PKCS5)
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
        "limit": "1"
    }

    Getecsurl = 'https://evs.{projectna}.myhuaweicloud.com/v2/{projectida}/cloudvolumes/detail'.format(
        projectna=project_name, projectida=project_id)

    res = requests.get(url=Getecsurl, headers=header, params=param)
    resq = json.loads(json.dumps(res.json()))
    vpcs = resq.get("volumes")
    num = resq.get("count")
    vpcs_list = []
    for i in range(0, num, 1000):
        param = {
            "project_id": project_id,
            "limit": "1000",
            "offset": i
        }
        Getecsurl = 'https://evs.{projectna}.myhuaweicloud.com/v2/{projectida}/cloudvolumes/detail'.format(
            projectna=project_name, projectida=project_id)

        res = requests.get(url=Getecsurl, headers=header, params=param)
        resq = json.loads(json.dumps(res.json()))
        vpcs = resq.get("volumes")

        for vpc in vpcs:
            item = dict()
            tags_list = []
            item["id"] = vpc.get("id")
            item["name"] = vpc.get("name")
            if vpc.get("size"):
                item["size"] = vpc.get("size")  # 容量
            if vpc.get("status"):
                if str(vpc.get("status")) == "in-use":
                    item["status"] = "使用中"
                else:
                    item["status"] = vpc.get("status")
            if str(vpc.get("multiattach")):
                item["multiattach"] = str(vpc.get("multiattach"))  # 是否为共享盘
            if vpc.get("created_at"):
                item["created_at"] = vpc.get("created_at")   #
            if vpc.get("metadata").get('__system__encrypted'):   #
                item["decrypt"] = vpc.get(
                    "metadata").get('__system__encrypted')
            else:
                item["decrypt"] = "0"
            if vpc.get("volume_image_metadata").get('image_name'):
                item["image_name"] = vpc.get(
                    "volume_image_metadata").get('image_name')  # 镜像
            if vpc.get("volume_type"):
                item["volume_type"] = vpc.get("volume_type")  # 云硬盘类型
            if vpc.get("volume_type") == "SSD":
                item["IOPSa"] = "33000"
                item["IOPSmax"] = "8000"
            elif vpc.get("volume_type") == "ESSD":
                item["IOPSa"] = "128000"
                item["IOPSmax"] = "64000"
            elif vpc.get("volume_type") == "SAS":
                item["IOPSa"] = "5000"
                item["IOPSmax"] = "5000"
            elif vpc.get("volume_type") == "GPSSD":
                item["IOPSa"] = "20000"
                item["IOPSmax"] = "16000"
            else:
                item["IOPSa"] = "2200"
                item["IOPSmax"] = "2200"
            if vpc.get("metadata").get('hw:passthrough'):  # 磁盘模式
                item["diskMode"] = vpc.get("metadata").get('hw:passthrough')
            else:
                item["diskMode"] = "false"
            if vpc.get("bootable"):
                item["bootable"] = vpc.get("bootable")  # 磁盘属性
                if str(vpc.get("bootable")) == "true":
                    item["bootable"] = "启动盘"
                else:
                    item["bootable"] = "非启动盘"
            if vpc.get('attachments'):
                item["server_id"] = [i.get('server_id')
                                     for i in vpc.get('attachments')]
                serverids = [i.get('server_id')
                             for i in vpc.get('attachments')]
                server_name = []
                for i in serverids:
                    Getecsurl = 'https://ecs.{projectna}.myhuaweicloud.com/v1/{projectida}/cloudservers/{server_id}'.format(
                        projectna=project_name, projectida=project_id, server_id=i)
                    res = requests.get(
                        url=Getecsurl, headers=header, params=param)
                    resq = json.loads(json.dumps(res.json()))
                    vpcs = resq.get("server")
                    servername = vpcs.get('name')
                    server_name.append(servername)
                item["server_name"] = server_name
            item["region"] = project_name   #
            item["enterprise_project_id"] = vpc.get(
                'enterprise_project_id')  # 企业项目ID
            item["availability_zone"] = vpc.get('availability_zone')
            if vpc.get('tags'):
                tag = vpc.get('tags')
                for i, j in tag.items():
                    m = '{}={}'.format(i, j)
                    tags_list.append(m)
                item["tags"] = tags_list
                for i in tags_list:
                    if "PDT" in str(i.split('=')[0]):
                        item["product"] = i.split('=')[1]
                    if "PJT" in str(i.split('=')[0]):
                        item["project"] = i.split('=')[1]
            vpcs_list.append(item)
    msg_dict = dict()
    msg_dict["CIT_CloudDrive"] = vpcs_list
    msg = json.dumps(msg_dict, ensure_ascii=False)
    return msg


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('--domainname', type=str,dest='domainname')
    parser.add_option('--username', type=str,dest='username')
    parser.add_option('--userpasswd', type=str,dest='userpasswd')
    parser.add_option('--projectname', type=str,dest='projectname')
    parser.add_option('--projectid', type=str, dest='projectid')

    (options, args) = parser.parse_args()
    domainname = options.domainname
    username = options.username
    userpasswd = des_decrypt(options.userpasswd)
    # userpasswd = options.userpasswd
    projectname = options.projectname
    projectid = options.projectid
    dataStr = get_data(domainname, username, userpasswd,
                       projectname, projectid)  # , projectid

    print(dataStr)  # dataStr
