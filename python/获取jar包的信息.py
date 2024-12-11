#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import json
import subprocess
import paramiko
import sys
try:
    from TypeConversion import res  # 调用公共类，输入模块
    from TypeConversion import outPutTable  # 调用公共类，表格输出模块
except Exception as error:
    print(error)
    exit(1)
defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)

class hostResourcesUse(object):

    def __init__(self):
        # self.server_connect = mzCmdbQuery()
        self.connection_info = {"address": "192.168.1.100", "user": "root", "password": "xxxxxxxx"}
    def login_ssh_host(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if self.connection_info['user'] == "" or self.connection_info['password']:
            ssh.connect(self.connection_info['address'],username="root",password="xxxxxxxx",port=22,timeout=10)
        else:
            ssh.connect(self.connection_info['address'],username=self.connection_info['user'],password=self.connection_info['password'],port=22,timeout=10)
        #获取jar包的目录
        jar_name=self.zabbix_dict['jar_name']
        find_cmd = 'find /home/devops/  -name "{jar_name}"'.format(jar_name=jar_name)# |sed  "s#{jarname}##g'
        stdin, stdout, stderr = ssh.exec_command(find_cmd)
        jar_path = [jarname for jarname in stdout.readlines() if "backup" not in jarname][0]
        jar_path = (jar_path.replace("\n","")).replace(jar_name,"")
        #查找执行脚本名称
        find_file='/usr/bin/find {jar_path}  -maxdepth 1 -type f -name "*star*.sh" -print0 | xargs -0 -I {{}} basename {{}}'.format(jar_path=jar_path)
        # find_file='/usr/bin/find {jar_path}  -maxdepth 1 -type f -name "*star*.sh"'.format(jar_path=jar_path)
        stdin, stdout, stderr = ssh.exec_command(find_file)
        script="false"
        for sh_file in stdout.readlines():
            sh_file=sh_file.replace("\n","")
            # sh_file=sh_file.split('/')[-1].replace("\n","")
            if "restart.sh" == sh_file:
                script=sh_file
                break
            if "restar.sh" == sh_file:
                script=sh_file
                break
            if "start.sh" == sh_file:
                script=sh_file
                break
        ssh.close()
        if script=="false":
            print("未找到启动脚本")
        else:
            data={"jar_info":{"jar_path":jar_path,"jar_name":jar_name,"script":script}}
            print(json.dumps(data))

if __name__ == '__main__':
    instance = hostResourcesUse()
    instance.login_ssh_host()