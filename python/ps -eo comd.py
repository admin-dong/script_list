# ps -o cmd取进程
# 1、远程ssh上  
#  2.ps -eo  取信息 去所有进程的command信息   
# 3.信息取出来存远程设备本地文件  
# 4.如果之前有存在的文件 另外存一个新的文件  为after
# 5.对比before 跟after的差异  
# 6.输出这些差异 
# 8.删除befor 跟after 这俩文件


#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import paramiko
import sys
import logging
import os
try:
    from TypeConversion import res  # 调用公共类，输入模块
except Exception as error:
    print(error)
    exit(1)

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

class ssh_connect_ip(object):
    def __init__(self, iplist):
        self.iplist = iplist.split(',') if isinstance(iplist, str) else iplist

    def login_ssh_host(self):
        all_outputs = []  # 用于存储所有 IP 地址的命令输出
        private_key = paramiko.RSAKey.from_private_key_file('/home/devops/.ssh/id_rsa')  # 从指定路径加载私钥
        for ip in self.iplist:
            ip = ip.strip()  # 去除 IP 地址两端的空白字符
            ssh = paramiko.SSHClient()  # 创建一个 SSH 客户端
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 自动添加主机密钥策略
            try:
                ssh.connect(ip, username="ubuntu", pkey=private_key, port=22, timeout=10)  # 连接到指定的 IP 地址
            except Exception as e:
                print("Error connecting to %s: %s" % (ip, e))  # 打印连接错误信息
                continue  # 跳过当前 IP 地址，继续下一个

            try:
                # 获取上次重启时间
                last_boot_cmd = "who -b | awk '{print $3, $4}'"
                stdin, stdout, stderr = ssh.exec_command(last_boot_cmd)  # 执行命令
                exit_status = stdout.channel.recv_exit_status()  # 获取命令的执行返回状态码
                if exit_status == 0:
                    last_boot_time = stdout.read().decode('utf-8').strip()  # 读取命令输出并去除首尾空白
                else:
                    error_stdout = stderr.read().decode('utf-8').strip()  # 读取错误输出
                    print("Error command %s: exit status %s, error %s" % (ip, exit_status, error_stdout))
                    continue

                # 读取或创建上次重启时间记录文件
                boot_time_file = 'boot_time_{}.txt'.format(ip)
                if os.path.exists(boot_time_file):
                    with open(boot_time_file, 'r') as f:
                        recorded_boot_time = f.read().strip()
                else:
                    recorded_boot_time = ""

                # 比较上次记录的重启时间和当前获取的重启时间
                if recorded_boot_time == last_boot_time:
                    print("Machine %s has not been restarted." % ip)  # 打印机器未重启的信息
                else:
                    # 保存当前获取的重启时间
                    with open(boot_time_file, 'w') as f:
                        f.write(last_boot_time)
                    print("Machine %s has been restarted." % ip)  # 打印机器已重启的信息
                    # 获取所有进程的命令信息
                    ps_cmd = "ps -eo cmd"
                    stdin, stdout, stderr = ssh.exec_command(ps_cmd)  # 执行命令
                    exit_status = stdout.channel.recv_exit_status()  # 获取命令的执行返回状态码
                    if exit_status == 0:
                        output = stdout.read().decode('utf-8').strip()  # 读取命令输出并去除首尾空白
                        lines = output.split('\n')[1:]  # 去掉表头
                        commands = [line.strip() for line in lines if line.strip()]  # 去掉空行
                        all_outputs.append((ip, commands))  # 将 IP 地址和命令输出添加到结果列表中
                    else:
                        error_stdout = stderr.read().decode('utf-8').strip()  # 读取错误输出
                        print("Error command %s: exit status %s, error %s" % (ip, exit_status, error_stdout))

            except Exception as e:
                print("Error executing command on %s: %s" % (ip, e))  # 打印命令执行错误信息
            finally:
                ssh.close()  # 确保关闭 SSH 连接

        return all_outputs  # 返回所有 IP 地址的命令输出

def save_to_file(data, file_path):
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, ensure_ascii=False)
        print("Data saved to %s" % file_path)
    except Exception as e:
        print("Error saving data to %s: %s" % (file_path, e))

def compare_files(before_file, after_file):
    try:
        with open(before_file, 'r') as f:
            before_data = json.load(f)
        with open(after_file, 'r') as f:
            after_data = json.load(f)

        added = {}
        removed = {}

        # 比较进程差异
        for ip in before_data:
            if ip in after_data:
                before_set = set(before_data[ip])
                after_set = set(after_data[ip])
                added[ip] = list(after_set - before_set)
                removed[ip] = list(before_set - after_set)
            else:
                removed[ip] = before_data[ip]

        for ip in after_data:
            if ip not in before_data:
                added[ip] = after_data[ip]

        return added, removed
    except Exception as e:
        print("Error comparing files %s and %s: %s" % (before_file, after_file, e))
        return {}, {}

def delete_files(*files):
    for file in files:
        try:
            if os.path.exists(file):
                os.remove(file)
                print("File %s deleted" % file)
        except Exception as e:
            print("Error deleting file %s: %s" % (file, e))

def rename_file(src, dst):
    try:
        if os.path.exists(src):
            os.rename(src, dst)
            print("File %s renamed to %s" % (src, dst))
    except Exception as e:
        print("Error renaming file %s to %s: %s" % (src, dst, e))

if __name__ == '__main__':
    #iplist = ["106.75.241.55", "106.75.252.127", "106.75.233.215"]
    iplist=res.get('iplist')
    ssh_connector = ssh_connect_ip(iplist)
    results = ssh_connector.login_ssh_host()

    all_outputs = {}
    for ip, output in results:
        if output is not None:
            all_outputs[ip] = output
        else:
            print("Error on %s: no process info" % ip)

    before_file = 'processes_before.json'
    after_file = 'processes_after.json'

    if os.path.exists(before_file):
        if all_outputs:
            save_to_file(all_outputs, after_file)
            added, removed = compare_files(before_file, after_file)

            # 仅打印重启设备的进程差异信息
            for ip in all_outputs.keys():
                if ip in added or ip in removed:
                    #print("Processes changed for %s:" % ip)
                    print("--begin--")
                    print("Added processes:", json.dumps({ip: added.get(ip, [])}, ensure_ascii=False))
                    print("Removed processes:", json.dumps({ip: removed.get(ip, [])}, ensure_ascii=False))
                    
            print("--end--")
            delete_files(before_file)
            rename_file(after_file, before_file)
        else:
            print("No machines have been restarted.")
    else:
        if all_outputs:
            save_to_file(all_outputs, before_file)
            print("No previous file found, saved current data to %s" % before_file)
        else:
            print("No machines have been restarted.")
