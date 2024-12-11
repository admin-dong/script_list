#!/usr/bin/python
# -*- coding: utf-8-*-
import os
import subprocess
import paramiko
import sys
import json
import requests
from pyDes import *
from optparse import OptionParser
from binascii import a2b_hex
try:
    from TypeConversion import res  # 调用公共类，输入模块
    from TypeConversion import outPutTable  # 调用公共类，表格输出模块
except Exception as error:
    print error
    exit(1)
reload(sys)
sys.setdefaultencoding('utf8')

def des_decrypt(message):
    k = des('shdevopsshdevops', ECB, padmode=PAD_PKCS5)
    return k.decrypt(a2b_hex(message)).decode('utf8')
def feishu_webhook(ip,project,env,message):
    url = "##飞书webhook"
    payload_message = {
    "msg_type": "interactive",
    "card": {
        "elements": [{
                "tag": "div",
                "text": {
                        "content": message,
                        "tag": "lark_md"
                }
        }],
        "header": {
                "title": {
                        "content": "{} {} {} 中间件,服务状态告警".format(project,env,ip),
                        "tag": "plain_text"
                },
                "template":"red" # 卡片标题颜色
        }
    }
    }
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=json.dumps(payload_message))
    return response

def ssh_client(hostname,ip,project,env,user,password,deployMiddleware,servicelist):
    middleware_list = []
    service_list = []
    middleware_list_err = []
    service_list_err = []
    item = dict()
    item['hostname'] = hostname
    item['hostip'] = ip
    item['project'] = project
    item['env'] = env
    ssh = paramiko.SSHClient()
    # 允许连接不在know_hosts文件中的主机
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # 建立连接
    ssh.connect(ip, username=user, port=22, password=password)
    if deployMiddleware != []:
        for Middleware in deployMiddleware:
            Middlewareitem = dict()
            command="systemctl status {}".format(Middleware)
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(command)
            Middlewareitem['name'] = Middleware
            if Middleware != "ui":
                if "running"  in ssh_stdout.read():
                    Middlewareitem['status'] = "active"
                else:
                    Middlewareitem['status'] = "inactivity"
                    middleware_list_err.append(Middleware)
                middleware_list.append(Middlewareitem)

    if servicelist != []:
        for service in servicelist:
            serviceitem = dict()
            command="ps -ef |grep {} | grep -v grep".format(service)
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(command)
            serviceitem['name'] = service
            if service in ssh_stdout.read():
                serviceitem['status'] = "active"
            else:
                serviceitem['status'] = "inactivity"
                service_list_err.append(service)
            service_list.append(serviceitem)
    ssh.close()
    item['middlewareStatus'] = middleware_list
    item['serviceStatus'] = service_list
    alarm = ""
    if middleware_list_err != [] and service_list_err != []:
        item['middleware_remark'] = '{} 中间件运行状态不为: active (running)'.format(','.join(middleware_list_err))
        item['service_remark'] = '{} 服务未存活'.format(','.join(service_list_err))
        alarm = '{} {} {} {}\n{}\n{}'.format(project,env,hostname,ip,item['middleware_remark'],item['service_remark'])
    if middleware_list_err != [] and service_list_err == []:
        item['middleware_remark'] = '{} 中间件运行状态不为: active (running)'.format(','.join(middleware_list_err))
        alarm = '{} {} {} {}\n{}'.format(project,env,hostname,ip,item['middleware_remark'])
    if middleware_list_err == [] and service_list_err != []:
        item['service_remark'] = '{} 服务未存活'.format(','.join(service_list_err))
        alarm = '{} {} {} {}\n{}'.format(project,env,hostname,ip,item['service_remark'])
    if middleware_list_err == [] and service_list_err == []:
        item['middleware_remark'] = ""
        item['service_remark'] = ""      
    if alarm != "":
        feishu_webhook(ip,project,env,alarm)
    return item

if __name__ == '__main__':
    hostname = res.get("hostname")
    hostip = res.get('hostip')
    project = res.get('project')
    env = res.get('env')
    user = res.get('user')
    password = des_decrypt(res.get('password'))
    deployMiddleware = res.get('deployMiddleware')
    deployService = res.get('deployService')
    status_list = [] 
    sshdata = ssh_client(hostname,hostip,project,env,user,password,deployMiddleware,deployService)
    status_list.append(sshdata)
    print(json.dumps({"CIT_deployliststatus":status_list},ensure_ascii=False,indent=2))
    