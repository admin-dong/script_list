
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
        ssh.connect(ssh_host,username=ssh_user,password=ssh_pwd,port=22,timeout=10)

        #获取cpu占用top3 进程id
        cpu_cmd = "ps -aux --sort=-%cpu | head -4 | tr -s ' ' | cut -d ' ' -f 2"
        stdin, stdout, stderr = ssh.exec_command(cpu_cmd)
        cpu = stdout.readlines()
        cpu.remove('PID\n')
        pid_list = [i.replace('\n','') for i in cpu]

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
            command = "ps -p {} -o %cpu,cmd".format(pid)
            stdin, stdout, stderr = ssh.exec_command(command)
            cpu_use_obj = stdout.readlines()
            cpu_use_course = '  '.join(cpu_use_obj).split(' ')
            cpu_use_list = [x for x in cpu_use_course if x not in ["","%CPU","CMD\n"]]

            cpu_use = cpu_use_list[0] + '%'

            cpu_use_list.pop(0)

            command = ' '.join(cpu_use_list)

            process.append(
                {
                    'pid':pid,
                    'pName':pName,
                    'port':port,
                    'use':cpu_use,
                    'command':command
                }
            )            
        ssh.close()
        return process
    

if __name__ == '__main__':
    instance = hostResourcesUse()
