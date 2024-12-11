
#-*- coding: utf-8 -*-  
#!/usr/bin/python

'''
Descripttion: 
Parameter: 
Author: liliangliang
Date: 2023-12-27 11:01:50
'''

import paramiko
import json
import re
import sys
from connect import mzCmdbQuery
from retry import retry

defaultencoding = "utf-8"
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)


class hostResourcesUse(object):

    def __init__(self):
        self.server_connect = mzCmdbQuery()

    #ssh登录目标主机
    @retry(tries=3,delay=5)  
    def login_ssh_host(self,server):

        connect_host = self.server_connect.get_alarmServer_task(server)

        ssh_host = connect_host['address']
        ssh_user = connect_host['user']
        ssh_pwd = connect_host['password']

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host,username=ssh_user,password=ssh_pwd,port=22,timeout=5)

        #获取内存占用top3 进程id
        memory_cmd = "ps -aux --sort=-%mem | head -4 | tr -s ' ' | cut -d ' ' -f 2"
        stdin, stdout, stderr = ssh.exec_command(memory_cmd)
        memory = stdout.readlines()
        memory.remove('PID\n')
        pid_list = [i.replace('\n','') for i in memory]

        #获取内存占用top3 进程名
        process = []
        
        for pid in pid_list:
            
            #获取进程名称
            command = 'ps -p {} -o comm='.format(int(pid))
            stdin, stdout, stderr = ssh.exec_command(command)
            pName = stdout.readline().replace('\n','')

            #获取进程端口
            command = 'sudo netstat -tulnp | grep {}'.format(int(pid))
            stdin, stdout, stderr = ssh.exec_command(command)
            port_obj = stdout.readlines()
            port_course = ' '.join(port_obj).split(' ')
            port_list = [x for x in port_course if x != '']

            if port_list != []:
                port = re.search(r':([^:]*)$', port_list[3]).group(1)
            else:
                port = ''

            #获取进程详细信息
            command = "ps -p {} -o %mem,cmd".format(pid)
            stdin, stdout, stderr = ssh.exec_command(command)
            memory_use_obj = stdout.readlines()
            memory_use_course = '  '.join(memory_use_obj).split(' ')
            memory_use_list = [x for x in memory_use_course if x not in ["","%MEM","CMD\n"]]

            memory_use = memory_use_list[0] + '%'

            memory_use_list.pop(0)

            command = ' '.join(memory_use_list)

            process.append(
                {
                    'pid':pid,
                    'pName':pName,
                    'port':port,
                    'use':memory_use,
                    'command':command
                }
            )  
        ssh.close()
        return process
        

if __name__ == '__main__':
    instance = hostResourcesUse()


#模板


#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Descripttion: 
Parameter: 
Author: liliangliang
Date: 2023-12-28 10:07:22
'''

import requests
import json
import sys
import ssl
from pysnmp.hlapi import *

defaultencoding = "utf-8"
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)

ssl._create_default_https_context = ssl._create_unverified_context

class pushNotification(object):

    def __init__(self):
        
        pass


    def elements_task(self,IP,data):
        
        content = []

        content.append({"tag": "div","text": {"content": IP,"tag": "plain_text"}})
        content.append({"tag": "hr"})

        for items in data:
            pid = items['pid']
            pName = items['pName']
            port = items['port']
            use = items['use']
            command = items['command']

            content_obj = "进程id：{pid}\n进程名称：{pName}\n端口：{port}\n内存使用：{use}\n命令：{command}".format(pid=pid,pName=pName,port=port,use=use,command=command)

            content.append(
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": content_obj
                        }
                    ]
                }
            )
            content.append({"tag": "hr"})
        return content


    def Post_Temperature_feishu(self,webhook,title,elements):

        header = {'Content-Type': 'application/json'}
        data = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "template": "red",
                    "title": {
                        "content": title,
                        "tag": "plain_text"
                    }
                },
                "elements": elements
            }
        }
        response = requests.post(url=webhook, headers=header, data=json.dumps(data), verify=False)
        return response.text

if __name__ == '__main__':
    instance = pushNotification()