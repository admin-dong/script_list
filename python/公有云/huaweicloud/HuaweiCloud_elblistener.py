
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
def get_data(domainname, username, userpasswd, projectname, projectid): #
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
                    "name": domain_name        #IAM用户所属账号名
						},
						"name": user_name,             #IAM用户名
						"password": user_passwd      #IAM用户密码
					}
				}
			},
			  "scope": {
				    "project": {
                "name": project_name               #项目名称
            }
        }
    }
}
    header = {
        "User-Agent":"test",
        "Content-Type":"application/json"
        }
    tokenurl = 'https://iam.{projectna}.myhuaweicloud.com/v3/auth/tokens'.format(projectna = project_name)
    req = requests.post(url = tokenurl,data=json.dumps(reqdata),headers=header)
    token = req.headers["X-Subject-Token"]

    header["X-Auth-Token"] = token

    param = {
		"project_id":project_id,
        "limit":"2000"
    }
	
    Getecsurl = 'https://elb.{projectna}.myhuaweicloud.com/v2/{projectida}/elb/listeners'.format(projectna = project_name,projectida = project_id)

    res = requests.get(url = Getecsurl,headers = header,params = param)
    msg_dict = json.loads(json.dumps(res.json()))
    jtqdata_list = []
    ser_id = []
    vpcs = msg_dict.get("listeners")
    jtqids = [i.get('id') for i in msg_dict.get("listeners")]
    num_id = jtqids[-1]
    ser_id.append(num_id)
    jtqdata_list.append(vpcs)
    num = 1
    vpcs_list = []
    while num < 10000:
        num_id = ser_id[num-1]
        header["X-Auth-Token"] = token
        paramu = {
                "project_id":project_id,
                "limit":"2000",
                "marker":num_id
        }
        testurl = 'https://elb.{projectna}.myhuaweicloud.com/v2/{projectida}/elb/listeners'.format(projectna = project_name,projectida = project_id)
        reas = requests.get(url = testurl,headers = header,params = paramu)
        msgdict = json.loads(json.dumps(reas.json()))
        jtqdata = msgdict.get("listeners")
        jtqid = [i.get('id') for i in msgdict.get("listeners")]
        if jtqid != []:
            bbb = jtqid[-1]
            jtqdata_list.append(jtqdata)
            ser_id.append(bbb)
            num += 1
        else:
            break
    for u in jtqdata_list:
        for vpc in u:
            item = dict()
            item["id"] = vpc.get("id")
            item["overdue"] = "true"
            item["name"] = vpc.get("name")
            if vpc.get("loadbalancers"):
                item["loadbalancers"] = vpc.get("loadbalancers")[0].get('id')
                loadbalancers = vpc.get("loadbalancers")[0].get('id')
                param = {
	            	"project_id":project_id,
                    "loadbalancer_id":loadbalancers
                }
    
                loadbalancera = 'https://elb.{projectna}.myhuaweicloud.com/v2/{projectida}/elb/loadbalancers/{loadbalancer_id}'.format(projectna = project_name,projectida = project_id,loadbalancer_id =loadbalancers)
                elbs = requests.get(url = loadbalancera,headers = header,params = param)
                elb = json.loads(json.dumps(elbs.json()))
                if elb.get('loadbalancer').get('name'):
                    item["elbname"] = elb.get('loadbalancer').get('name')
            if vpc.get("protocol_port"):
                item["protocol_port"] = vpc.get("protocol_port")   #监听端口
            if vpc.get("protocol"):
                item["protocol"] = vpc.get("protocol")   #协议
            if vpc.get("default_pool_id"):
                item["default_pool_id"] = vpc.get("default_pool_id")#
            if vpc.get('tags'):
                item["tags"] = vpc.get('tags')
                for i in vpc.get('tags'):
                    if "PDT" in str(i.split('=')[0]):
                        item["product"] = i.split('=')[1]
                    if "PJT" in str(i.split('=')[0]):
                        item["project"] = i.split('=')[1]
            vpcs_list.append(item)
    msg_dict = dict()
    msg_dict["CIT_LoadBalancerListener"] = vpcs_list
    msg = json.dumps(msg_dict)
    return msg

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('--domainname', type=str, dest='domainname')
    parser.add_option('--username', type=str, dest='username')
    parser.add_option('--userpasswd', type=str, dest='userpasswd')
    parser.add_option('--projectname', type=str, dest='projectname')
    parser.add_option('--projectid', type=str, dest='projectid')

    (options, args) = parser.parse_args()
    domainname = options.domainname
    username = options.username
    userpasswd = des_decrypt(options.userpasswd)
    #userpasswd = options.userpasswd
    projectname = options.projectname
    projectid = options.projectid

    dataStr = get_data(domainname, username, userpasswd, projectname, projectid)

    print(dataStr)  #dataStr
