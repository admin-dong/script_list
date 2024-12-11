
#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@LastDebugTime :2024/01/12 15:25:10,
@Env           :python2
"""
import requests
import json
import paramiko
import sys
import time
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

class reset_service(object):
    def __init__(self):
        #not in
        self.Not_list = [[],'',None]
        #流程传入组件
        self.jar_info=res.get('jar_info')
        self.connection_info =  res.get('connection_info') if res.get('connection_info') else ""

    def connetAndExec(self):
        '''
        远程到linux机器执行命令
        '''
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if self.connection_info['user'] == "" or self.connection_info['password']:
            username="root"
            password="xxxx"
        else:
            username=self.connection_info['user']
            password=self.connection_info['password']
        ssh.connect(self.connection_info['address'],username=username,password=password,port=22,timeout=10)
        if username != "root":
            cmd = "cd {jar_path} && sh {script}".format(jar_path=self.jar_info['jar_path'],script=self.jar_info['script'])
        if username == "root":
            cmd = 'cd {jar_path} && runuser -l devops {jar_path}{script}'.format(jar_path=self.jar_info['jar_path'],script=self.jar_info['script'])
        stdin,stdout,stderr =ssh.exec_command(cmd)

        #检查服务是否存活
        time.sleep(60)
        check_service='ps -ef|grep {jar_name} |grep -v "grep"'.format(jar_name=self.jar_info['jar_name'])
        stdin,stdout,stderr =ssh.exec_command(check_service)
        if stdout.readlines() != []:
            print("--begin--")
            print(json.dumps({"status":"true"}))
            print("--end--") 
        else:
            print("--begin--")
            print(json.dumps({"status":"false"}))
            print("--end--") 
        ssh.close()

if __name__ == '__main__':
    instance = reset_service()
    instance.connetAndExec()