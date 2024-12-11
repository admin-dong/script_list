
#!/usr/bin/python
# -*- coding: UTF-8 -*-

import json
import sys
import requests
from optparse import OptionParser
from pyDes import *
from binascii import a2b_hex
def des_decrypt(message):
    k = des('shqzshqz', ECB, padmode=PAD_PKCS5)
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
		    "project_id":project_id
    }
	
    Getecsurl = 'https://vpc.{projectna}.myhuaweicloud.com/v1/{projectida}/vpcs'.format(projectna = project_name,projectida = project_id)

    res = requests.get(url = Getecsurl,headers = header,params = param)

    msg_dict = json.loads(json.dumps(res.json()))
    vpcs = msg_dict.get("vpcs")
    vpcs_list = []
    for vpc in vpcs:
        tags_list = []
        item = dict()
        id = vpc.get("id")            #vpcid
        item["id"] = vpc.get("id")            #vpcid
        item["region"] = project_name
        paramaa = {
	    	"project_id":project_id,
            "vpc_id":id
        } 
        vpctagsurl = 'https://vpc.{projectna}.myhuaweicloud.com/v2.0/{projectida}/vpcs/{vpc_id}/tags'.format(projectna = project_name,projectida = project_id,vpc_id=id)
        vpcsubnets = requests.get(url = vpctagsurl,headers = header,params = paramaa)
        vpcsubnet = json.loads(json.dumps(vpcsubnets.json()))
        if vpcsubnet.get('tags'):
            for w in vpcsubnet.get('tags'):
                k = w.get('key')
                v = w.get('value')
                ta = '{}={}'.format(k,v)
                tags_list.append(ta)
            item["tags"] = tags_list
            for i in tags_list:
                if "PDT" in str(i.split('=')[0]):
                    item["product"] = i.split('=')[1]
                if "PJT" in str(i.split('=')[0]):
                    item["project"] = i.split('=')[1]
        item["name"] = vpc.get("name")        #vpc名称  
        if vpc.get("cidr"):
            item["cidr"] = vpc.get("cidr")        #虚拟私有云下可用子网的范围
        if vpc.get("status"):
            item["status"] = vpc.get("status")      #虚拟私有云的状态
        paramss = {
		    "project_id":project_id,
        } 
        routeurl = 'https://vpc.{projectna}.myhuaweicloud.com/v2.0/vpc/routes?vpc_id={id}'.format(projectna = project_name,id=id)
        routes = requests.get(url = routeurl,headers = header,)
        route = json.loads(json.dumps(routes.json()))
        if route.get('routes'):
            item["route_count"] =  len([i.get('id') for i in route.get('routes')])
        if vpc.get("enterprise_project_id"):
            item["enterprise_project_id"] = vpc.get("enterprise_project_id")          #项目ID
        paramsa = {
		    "project_id":project_id,
        } 
        subnetsurl = 'https://vpc.{projectna}.myhuaweicloud.com/v1/{projectida}/subnets?vpc_id={id}'.format(projectna = project_name,projectida=project_id,id=id)
        subnetse = requests.get(url = subnetsurl,headers = header,params = paramsa)
        subnet = json.loads(json.dumps(subnetse.json()))
        if subnet.get('subnets'):
            item["subnet_count"] =  len([i.get('id') for i in subnet.get('subnets')])        

        vpcs_list.append(item)
    msg_dict = dict()
    msg_dict["CIT_HuaweicloudVPC"] = vpcs_list
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
