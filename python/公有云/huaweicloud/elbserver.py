
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
    Getecsurl = 'https://elb.{projectna}.myhuaweicloud.com/v2/{projectida}/elb/pools'.format(projectna = project_name,projectida = project_id)
    res = requests.get(url = Getecsurl,headers = header,params = param)
    msg_dict = json.loads(json.dumps(res.json()))
    groupdata_list = []
    ser_id = []
    vpcs = msg_dict.get("pools")
    groupids = [i.get('id') for i in msg_dict.get("pools")]
    num_id = groupids[-1]
    ser_id.append(num_id)
    groupdata_list.append(vpcs)
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
        testurl = 'https://elb.{projectna}.myhuaweicloud.com/v2/{projectida}/elb/pools'.format(projectna = project_name,projectida = project_id)
        reas = requests.get(url = testurl,headers = header,params = paramu)
        msgdict = json.loads(json.dumps(reas.json()))
        groupdata = msgdict.get("pools")
        groupid = [i.get('id') for i in msgdict.get("pools")]
        if groupid != []:
            bbb = groupid[-1]
            groupdata_list.append(groupdata)
            ser_id.append(bbb)
            num += 1
        else:
            break
    for u in groupdata_list:
        for vpc in u:
            item = dict()
            ports_list = []
            port_list = []
            server_name_list = []
            jtq_list = []
            id = vpc.get("id")      
            item["id"] = vpc.get("id")      
            item["name"] = vpc.get("name")
            item["overdue"] = "true"
            if vpc.get("members"):
                members = [i.get('id') for i in vpc.get("members")]  #实例id列表
                item["members"] = [i.get('id') for i in vpc.get("members")]  #实例id列表
                for i in members:
                    paramaa = {
	                	"pool_id":id,
                        "member_id":i
                    }
                    serverurl = 'https://elb.{projectna}.myhuaweicloud.com/v2/{projectida}/elb/pools/{pool_id}/members/{member_id}'.format(projectna = project_name,projectida = project_id,pool_id = id,member_id=i)
                    servers = requests.get(url = serverurl,headers = header,params = param)
                    server = json.loads(json.dumps(servers.json()))
                    server_name = server.get('member').get('name')
                    ports = str(server.get('member').get('protocol_port'))
                    ports_list.append(ports)
                    server_name_list.append(server_name)
                item["port"] = list(set(ports_list))
                item["server_na"] = server_name_list  #实例名称列表
            if vpc.get("listeners"):
                listeners = [i.get('id') for i in vpc.get("listeners")] #关联监听器id列表
                item["listeners"] = [i.get('id') for i in vpc.get("listeners")] #关联监听器id列表
            
                for j in listeners:
                    param = {
	            	    "project_id":project_id,
                        "listener_id":j
                    }
                    loadbalancera = 'https://elb.{projectna}.myhuaweicloud.com/v2/{projectida}/elb/listeners/{listener_id}'.format(projectna = project_name,projectida = project_id,listener_id =j)
                    jtqs = requests.get(url = loadbalancera,headers = header,params = param)
                    jtq = json.loads(json.dumps(jtqs.json()))
                    listener_names = jtq.get('listener').get('name')
                    jtq_list.append(listener_names)
                item["listener_name"] = jtq_list #关联监听器名称
            if vpc.get("protocol"):
                item["pools"] = vpc.get("protocol")   #协议
            if vpc.get('tags'):
                item["tags"] = vpc.get('tags')
                for i in vpc.get('tags'):
                    if "PDT" in str(i.split('=')[0]):
                        item["product"] = i.split('=')[1]
                    if "PJT" in str(i.split('=')[0]):
                        item["project"] = i.split('=')[1]
            vpcs_list.append(item)
    msg_dict = dict()
    msg_dict["CIT_BackendServiceGroups"] = vpcs_list
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
