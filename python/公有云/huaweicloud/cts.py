
#!/usr/bin/python
# -*- coding: UTF-8 -*-

import json
import sys
import requests
from optparse import OptionParser
from pyDes import *
from binascii import a2b_hex
import time
import datetime
reload(sys)
sys.setdefaultencoding('utf8')
def des_decrypt(message):
    k = des('shdevopsshdevops', ECB, padmode=PAD_PKCS5)
    return k.decrypt(a2b_hex(message)).decode('utf8')
parser = OptionParser()
parser.add_option('--domainname', type=str,dest='domainname')
parser.add_option('--username', type=str, dest='username')
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


def des_decrypt(message):
    k = des('shdevopsshdevops', ECB, padmode=PAD_PKCS5)
    return k.decrypt(a2b_hex(message)).decode('utf8')


def get_data(domainname, username, userpasswd, projectname):  # , projectid
    domain_name = domainname
    user_name = username
    user_passwd = userpasswd
    project_name = projectname
    #project_id = projectid
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
    return token


token = get_data(domainname, username, userpasswd, projectname)
logdata = list()
marker_list = list()
header = {
    "User-Agent": "test",
    "Content-Type": "application/json"
}
header["X-Auth-Token"] = token
param = {
    "project_id": projectid
}
form = int(time.mktime(time.strptime((datetime.datetime.now(
)+datetime.timedelta(days=-3)).strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S"))*1000)
to = int(time.time()*1000)
Getecsurl = 'https://cts.{projectna}.myhuaweicloud.com/v3/{projectida}/traces?trace_type=system&limit=200&from={form}&to={to}'.format(
    projectna=projectname, projectida=projectid, form=form, to=to)
res = requests.get(url=Getecsurl, headers=header, params=param)

resa = json.loads(json.dumps(res.json()))
ldata = resa.get('traces')
for i in ldata:
    mlog = dict()
    if str(i.get('resource_id')):
        mlog['resource_id'] = i.get('resource_id')
        mlog['resource_name'] = i.get('resource_name')
        mlog['service_type'] = i.get('service_type')
        mlog['resource_type'] = i.get('resource_type')
        time1 = int(i.get('record_time') / 1000)
        mlog['record_time'] = str(time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(time1)))
        logdata.append(mlog)
if resa.get("meta_data").get("marker"):
    marker = resa.get("meta_data").get("marker")
    marker_list.append(marker)


def get_log(projectname, projectid, token, marker):
    # domain_name = domainname
    # user_name = username
    # user_passwd = userpasswd
    project_name = projectname
    project_id = projectid

    header["X-Auth-Token"] = token
    param = {
        "project_id": project_id
    }
    form = int(time.mktime(time.strptime((datetime.datetime.now(
    )+datetime.timedelta(days=-3)).strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S"))*1000)
    to = int(time.time()*1000)
    Getecsurl = 'https://cts.{projectna}.myhuaweicloud.com/v3/{projectida}/traces?trace_type=system&limit=200&next={mark}&from={form}&to={to}'.format(
        projectna=project_name, projectida=project_id, form=form, to=to, mark=marker)

    res = requests.get(url=Getecsurl, headers=header, params=param)
    resc = json.loads(json.dumps(res.json()))
    mdata = resc.get("traces")
    nlog_list = list()
    nn = "1"
    for i in mdata:
        item = dict()
        if str(i.get('resource_id')):
            item['resource_id'] = i.get('resource_id')
            item['trace_name'] = i.get('trace_name')
            item['resource_name'] = i.get('resource_name')
            item['service_type'] = i.get('service_type')
            item['resource_type'] = i.get('resource_type')
            time1 = i.get('record_time') / 1000
            item['record_time'] = str(time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(time1)))
            nlog_list.append(item)
    if resc.get("meta_data").get("marker"):
        marker = resc.get("meta_data").get("marker")

        return nlog_list, marker
    else:
        return nlog_list, nn


num = 1
while num <= 10000:
    if marker_list != []:
        marker = marker_list[-1]
        oo = get_log(projectname, projectid, token, marker)[0]
        num += 1
        if oo != []:
            for i in oo:
                logdata.append(i)
        moo = str(get_log(projectname, projectid, token, marker)[1])
        if moo != "1":
            marker_list.append(moo)
        else:
            break
    else:
        break

auth_url = 'http://10.230.211.219:9069/login/direct'
response = requests.post(
    url=auth_url,
    headers={
        'content-type': 'application/json',
        'accept': 'text/html,application/json',
    },
    data=json.dumps({
        'username': 'admin',
        'password': 'admin888'
    })
)
tokens = json.loads(response.text).get('param')

# net_list = []
def data(tokens,viewid,key):
    net_list = []
    # url = 'http://192.168.3.67:9069/view/direct'
    url = 'http://10.230.211.219:9069/view/direct'
    headersa = {
        'content-type': 'application/json',
        'accept': 'text/html,application/json',
        'Authorization': tokens
    }
    aaa = {"queryCondition": [],
          "viewid": viewid, 
          "startPage": 1, 
          "pageSize": 1,
          "moduleName":"查看",
          "name":"查看"
        }
    resp = requests.post(url = url, headers=headersa, data=json.dumps(aaa))
    eamm = resp.text.replace("\"success\":true,", "")
    ep = json.loads(eamm)
    total = ep.get('param').get('total')
    offsets = total/100
    offset = total % 100
    if offset != 0:
        offsets += 1
    for i in range(1, offsets+1):
        bbb = {"queryCondition": [],
          "viewid": viewid, 
          "startPage": i, 
          "pageSize": 1000,
          "moduleName":"查看",
          "name":"查看"
        }
        respa = requests.post(url = url, headers=headersa, data=json.dumps(bbb))
        datass = respa.text.replace("\"success\":true,", "")
        datas = json.loads(datass)
        for i in datas.get('param').get('content'):
            # ne = {"owningNetworkZone":i.get('owningNetworkZone'),
            #      "IPv4Network":i.get('IPv4Network')
            #      }
            net_list.append(i.get(key))
    return net_list
ecsdata = data(tokens,'072b0d139ffc4c02937b9841b4ff3a07','ecsid')
rdsdata = data(tokens,'b1cb0cb8541c4d12aa6877f01cc70f02','rdsid')
evsdata = data(tokens,'e9472f7075a346dd89f74eb209c876a1','id')
elbdata = data(tokens,'ce83dc5a42954e9c8b87606cf530c27e','elbid')
obsdata = data(tokens,'ce129f77efcf4038a61997316f912468','name')
eipdata = data(tokens,'bf686df7bb3148f4bfcc9467bd87396d','eipid')
vpcdata = data(tokens,'706df865684840e0be338f72843b1801','vpc_id')
dcsdata = data(tokens,'f5ecbfd4e0714ac3bd91d5b28fa299e4','dcsid')
ddsdata = data(tokens,'cb4db1a7385a42c5b6da42b6481c2cea','ddsid')

log_list = list()
ecs_list = list()
obs_list = list()
evs_list = list()
eip_list = list()
vpc_list = list()
elb_list = list()
dcs_list = list()
rds_list = list()
dds_list = list()
for i in logdata:
    ecsitem = dict()
    obsitem = dict()
    evsitem = dict()
    eipitem = dict()
    vpcitem = dict()
    elbitem = dict()
    dcsitem = dict()
    rdsitem = dict()
    ddsitem = dict()
    if i.get('trace_name'):
        if "deleteServer" in str(i.get('trace_name')) and i.get('resource_name') and str(i.get('resource_type')) == "ecs" and str(i.get('resource_id')) in ecsdata:
            ecsitem['id'] = i.get('resource_id')
            ecsitem['status'] = "delete"
            log_list.append(i)
            ecs_list.append(ecsitem)

        if "deleteBucket" in str(i.get('trace_name')) and i.get('resource_name') and str(i.get('resource_type')) == "bucket" and str(i.get('resource_name')) in obsdata:
            obsitem['name'] = i.get('resource_name')
            obsitem['status'] = "delete"
            obs_list.append(obsitem)
            log_list.append(i)

        if "deleteVolume" in str(i.get('trace_name')) and str(i.get('resource_type')) == "evs" and i.get('resource_name') and str(i.get('resource_id')) in evsdata:
            evsitem['id'] = i.get('resource_id')
            evsitem['status'] = "delete"
            evs_list.append(evsitem)
            log_list.append(i)

        if "deleteEip" in str(i.get('trace_name')) and i.get('resource_name') and str(i.get('resource_type')) == "eip" and str(i.get('resource_id')) in eipdata:
            eipitem['id'] = i.get('resource_id')
            eipitem['status'] = "delete"
            eip_list.append(eipitem)
            log_list.append(i)
  
        if "deleteVpc" in str(i.get('trace_name')) and i.get('resource_name') and str(i.get('resource_type')) == "vpc" and str(i.get('resource_id')) in vpcdata:
            vpcitem['id'] = i.get('resource_id')
            vpcitem['status'] = "delete"
            vpc_list.append(vpcitem)
            log_list.append(i)
  
        if "deleteLoadbalancer" in str(i.get('trace_name')) and i.get('resource_name') and str(i.get('resource_type')) == "loadbalancer" and str(i.get('resource_id')) in elbdata:
            elbitem['id'] = i.get('resource_id')
            elbitem['status'] = "delete"
            elb_list.append(elbitem)
            log_list.append(i)

        if "deleteDCSInstance" in str(i.get('trace_name')) and i.get('resource_name') and str(i.get('resource_type')) == "Redis" and str(i.get('resource_id')) in dcsdata:
            dcsitem['id'] = i.get('resource_id')
            dcsitem['status'] = "delete"
            dcs_list.append(dcsitem)
            log_list.append(i)
   
        if "deleteInstance" in str(i.get('trace_name')) and i.get('resource_name') and str(i.get('resource_type')) == "instance" and str(i.get('resource_id')) in rdsdata:
            rdsitem['id'] = i.get('resource_id')
            rdsitem['status'] = "delete"
            rds_list.append(rdsitem)
            log_list.append(i)
        
        if "ddsDeleteInstance" in str(i.get('trace_name')) and i.get('resource_name') and str(i.get('resource_type')) == "instance" and str(i.get('resource_id')) in ddsdata:
            ddsitem['id'] = i.get('resource_id')
            ddsitem['status'] = "delete"
            dds_list.append(ddsitem)
            log_list.append(i)
update = dict()
update["CIT_HuaweicloudECS"] = ecs_list
update["CIT_OBS"] = obs_list
update["CIT_CloudDrive"] = evs_list
update["CIT_EIP"] = eip_list
update["CIT_HuaweicloudVPC"] = vpc_list
update["CIT_LoadBalancer"] = elb_list
update["CIT_DCS"] = dcs_list
update["CIT_HuaweicloudRDS"] = rds_list
update["CIT_DDS"] = dds_list
update["CIT_huaweicloudlog"] = log_list
print json.dumps(update, ensure_ascii=False)
