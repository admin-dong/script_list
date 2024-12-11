
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
def get_data(domainname, username, userpasswd):
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
                            "name": domain_name        #IAM用户所属账号名
						},
                        "name": user_name,             #IAM用户名
						"password": user_passwd,      #IAM用户密码

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
        "User-Agent":"test",
        "Content-Type":"application/json"
        }
    tokenurl = 'https://iam.myhuaweicloud.com/v3/auth/tokens'

    req = requests.post(url = tokenurl,data=json.dumps(reqdata),headers=header)
    token = req.headers["X-Subject-Token"]
    header["X-Auth-Token"] = token

    Getecsurl = 'https://eps.myhuaweicloud.com/v1.0/enterprise-projects' 

    res = requests.get(url = Getecsurl,headers = header) #
    requ = json.dumps(res.json())
    msg_dict = json.loads(requ)
    num = msg_dict.get('total_count')
    vpcs_list = []
    offsets = num/1000
    offset = num%1000
    if offset != 0 :
        offsets += 1
    for i in range(1,offsets+1):

        Getecsur = 'https://eps.myhuaweicloud.com/v1.0/enterprise-projects' 
        ree = requests.get(url = Getecsur,headers = header) #
        requs = json.loads(json.dumps(ree.json()))
        vpcs = requs.get("enterprise_projects")

        for vpc in vpcs:
            item = dict()
            item["id"] = vpc.get("id")
            item["name"] = vpc.get("name")        #
            if vpc.get('type'):
                item["type"] = vpc.get("type")
            if vpc.get("status"):
                item["status"] = vpc.get("status") #
            if vpc.get("created_at"):
                item["created_at"] = vpc.get("created_at")  

            vpcs_list.append(item)
    msg_dict = dict()
    msg_dict["CIT_Enterpriseproject"] = vpcs_list
    msg = json.dumps(msg_dict)
    return msg

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('--domainname', type=str, dest='domainname')
    parser.add_option('--username', type=str, dest='username')
    parser.add_option('--userpasswd', type=str, dest='userpasswd')

    (options, args) = parser.parse_args()
    domainname = options.domainname
    username = options.username
    #userpasswd = options.userpasswd
    userpasswd = des_decrypt(options.userpasswd)
    dataStr = get_data(domainname, username, userpasswd)

    print(dataStr)

