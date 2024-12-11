
#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@FileName    :unix_discover.py
@Describe    :

'''

import json
import sys
import re
import os
import platform
import socket
from utils import *
from optparse import OptionParser

defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)

class Host(object):
    def __init__(self):

        self.discorver_ip = socket.gethostbyname(self.__hostname())
        self.os_version = self.__os_version()
        self.os_type = self.__os_type()
    
    @exception_None
    def __os_version(self):
        return platform.platform()

    @exception_None
    def __os_type(self):
        return platform.system()

    @exception_None
    def __hostname(self):
        return socket.gethostname()

    def __kernelversion(self):
        return platform.processor()

    def getMemary(self):
        info_lines=execute("cat /proc/meminfo | grep MemTotal",300)
        return str(int(info_lines[0].split()[1])/1024)+'MB'

    def getTimeZone(self):
        timeZone=execute('timedatectl | grep "Time zone"',3000)
        return timeZone[0].split(":")[1].replace("\n","").replace(" ","")

    def __host(self):
        return {
            'CIT_Host': [
                {
                    'ManageIp': self.discorver_ip,
                    'HostName': self.__hostname(),
                    'OSType': self.__os_type().upper(),
                    'OperateSystem': self.__os_version(),
                    'kernelversion':self.__kernelversion(),
                    "Memory":self.getMemary(),
                    "Status":"Running",
                    "timeZone":self.getTimeZone()
                    # 'valueMethod': 'auto',
                    # 'dataStatus': 'efficient',
                    # 'valueMethodAdd': self.discorver_ip
                }
            ]
        }


    def __processers(self):
        processers = []
        info_str = open('/proc/cpuinfo', 'r').read().split('\n\n')[:-1]
        for item in info_str:
            instance = {
                'discorver_ip': self.discorver_ip,
                'id': re.search(r'(?<=processor\t: ).+(?=\n)', item).group() if re.search(r'(?<=processor\t: ).+(?=\n)', item) else None ,
                'model': re.search(r'(?<=model name\t: ).+(?=\n)', item).group() if re.search(r'(?<=model name\t: ).+(?=\n)', item) else None,
                'mhz': re.search(r'(?<=cpu MHz\t\t: ).+(?=\n)', item).group() + 'MHz' if re.search(r'(?<=cpu MHz\t\t: ).+(?=\n)', item) else None,
                'cpu_type': re.search(r'(?<=vendor_id\t: ).+(?=\n)', item).group() if re.search(r'(?<=vendor_id\t: ).+(?=\n)', item) else None,
                'cores': re.search(r'(?<=cpu cores\t: ).+(?=\n)', item).group() if re.search(r'(?<=cpu cores\t: ).+(?=\n)', item) else None,
                'valueMethod': 'auto',
                'dataStatus': 'efficient',
                'valueMethodAdd': self.discorver_ip
            }
            # processers.append({key:value for key,value in instance.items() if value})
            result = {}
            for key, value in instance.items():
                if value:
                    result.update({ key: value })
            
            processers.append(result)
        
        return {
            'CIT_cpu': processers,
        }
    
    def __file_system(self):
        file_system_list = []
        file_system_lines = execute("df -ThP|grep -v Filesystem", 300)
        if file_system_lines:
            for item in file_system_lines:
                instance = {}
                if isinstance(item, bytes):
                    line = item.decode()
                elif isinstance(item, str):
                    line = item
                info = ' '.join(line.split()).split(' ')
                instance.update({
                    'discorver_ip': self.discorver_ip,
                    'filesystem': info[0],
                    'filesystem_type': info[1],
                    'size': info[2],
                    'mount_path': info[6],
                    'valueMethod': 'auto', 
                    'dataStatus': 'efficient',
                    'valueMethodAdd': self.discorver_ip
                })
                file_system_list.append(instance)
        
        return {
            'CIT_fileSystem': file_system_list,
        }
    

    def __fc_port(self):
        fc_ports = []
        fc_state = os.path.exists('/sys/class/fc_host/')
        if fc_state:
            files = [item.strip('\n') for item in execute('ls /sys/class/fc_host/*', 300) ]
            for item in files:
                wwn = open(item+'/port_name', "r")
                instance = {
                    'discorver_ip': self.discorver_ip,
                    'wwn': wwn,
                    'valueMethod': 'auto', 
                    'dataStatus': 'efficient',
                    'valueMethodAdd': self.discorver_ip
                }
                fc_ports.append(instance)
        
        return {
            'CIT_Fcport': fc_ports
        }

    def get_countdisks(self,result):
        count=[i["size"] for i in result["CIT_fileSystem"]]
        countdisks=0
        for i in count:
            if i.endswith("G"):
                countdisks+=float(i[0:-1])
            elif i.endswith("M"):
                countdisks+=float(i[0:-1]) / 1024
        return str(int(countdisks))+"GB"

    
    def output(self):
        result = {}
        result.update(self.__fc_port())
        result.update(self.__file_system())
        result.update(self.__processers())
        result.update(self.__host())
        result["CIT_Host"][0]["sumcpucore"]=str(sum([int(i['cores']) for i in result["CIT_cpu"]]))
        result["CIT_Host"][0]["countdisks"]=self.get_countdisks(result)
        print(beautyJson({"CIT_Host":result["CIT_Host"]}))

        
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--ip', type=str, help='unix IP')
    (options, args) = parser.parse_args()
    ip = options.ip
    instance = Host()
    instance.output()