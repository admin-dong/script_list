# !/usr/bin/env python
# -*- coding: utf-8 -*-
# # python2的转换
# reload(sys)
# sys.setdefaultencoding('utf8')

import requests
import json
import paramiko
import sys
import logging
#try:
#    from TypeConversion import res  # 调用公共类，输入模块
#    from TypeConversion import outPutTable  # 调用公共类，表格输出模块
#except Exception as error:
#    print(error)
#    exit(1)

defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)
# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# 为 paramiko.transport 添加默认的日志处理程序，并设置日志级别为 ERROR 以忽略警告
paramiko_logger = logging.getLogger("paramiko.transport")
paramiko_logger.setLevel(logging.ERROR)
paramiko_logger.addHandler(logging.NullHandler())

##传参ip给列表
##遍历列表里面的ip
##查看列表里面的ip的进程
##进程信息json格式输出
# UID：运行该进程的用户ID。
# PID：进程ID。
# PPID：父进程ID。
# C：CPU使用率（有时可能代表优先级）。
# STIME：进程启动的时间。
# TTY：进程关联的终端（如果有的话）。
# TIME：进程使用的CPU时间。
# CMD：启动该进程的命令。



class ssh_connect_ip(object):
    def __init__(self,iplist,connection_info):
        self.iplist= iplist 
        self.connection_info= connection_info
    def login_ssh_host(self):
        all_outputs = []
        for ip in self.iplist:
            try:
                ssh=paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                if not self.connection_info['user'].strip() or not self.connection_info['password'].strip():
                    ssh.connect(ip,username="devops",password="devops8866.",port=22,timeout=20)
                    print("使用默认密码")
                else:
                    ssh.connect(ip,username=self.connection_info['user'],password=self.connection_info['password'],port=22,timeout=10)
                    print("使用自定义密码")
            except Exception as e:
                ssh.close()
                print("Error connecting to %s %s" %(ip,e))
            try:    
                ps_process="ps -ef"
                stdin, stdout, stderr = ssh.exec_command(ps_process) ##执行命令
                exit_status=stdout.channel.recv_exit_status() ##获取命令的执行返回状态码
                if exit_status==0:
                    output = stdout.read().decode('utf-8').strip() ## 读取命令输出
                    lines = [line.split() for line in output.split('\n')]# 将输出按行分割
                    headers = lines[0]  ## 第一行是列头 
                    ##解析剩余的行
                    processes=[]
                    for line in lines[1:]:
                        process=dict(zip(headers,line))
                        processes.append(process)
                    output=json.dumps(processes,indent=4,ensure_ascii=False)
                    ssh.close()
                    all_outputs.append((ip, output))
                else:
                    error_stdout=stderr.read().decode('utf-8').strip() ##错误返回
                    print("error command %s : exit status %s, error %s" %(ip ,exit_status,error_stdout)) #打印
            except Exception as e:
                print("error command %s %s",(ip,e)) #ip 与异常       
        return all_outputs



if __name__ == '__main__':
    iplist = ["10.1.2.39","10.1.2.40","10.1.2.41"]
    connection_info = {
        'user': " ",  # 如果为空，则使用默认用户名和密码
        'password': " "  # 如果为空，则使用默认密码
    }
    ssh_connector=ssh_connect_ip(iplist,connection_info)
    results=ssh_connector.login_ssh_host() ##调用方法
    for ip, output in results:
        if output is not None:
            print("Processes on %s:\n%s" % (ip, output))  # 打印
        else:
            print("error on %s: no process info"% (ip)) ##错误信息

    all_results = {}
    for ip, output in results:
        if output is not None:
            all_results[ip] = json.loads(output)  # 将 JSON 字符串转换为字典
        else:
            all_results[ip]= None
    if any(value is not None for value in all_results.values()):
        with open('all_processes.json', 'w') as file:
            json.dump(all_results, file, indent=4, ensure_ascii=False)
            print("All process information saved to all_processes.json")# 将所有结果保存到一个文件中
    else:
        print("No valid process information available, not saving the JSON file.")#上个数据为空不需要保存json文件
