# -*- coding: UTF-8 -*-
import os
import json
from optparse import OptionParser
from IPy import IP

def IPSplit_d(line):
        dic = []
        ip = IP(line)
        for x in ip:
            dic.append(str(x))
        return dic

def ipy(netSegment):
    li = []
    ips = IPSplit_d(netSegment)
    ips.pop(0)
    for ip in ips:
        result = os.popen('ping -c 1 -W 1 %s' % (ip)).read()
        dic = dict()
        if 'ttl' in result:
            dic['ipAddress'] = ip
            #dic['poc_prod'] = 'poc_prod'
            #dic['status'] = 'use'
            dic['Network'] = netSegment
        else:
            dic['ipAddress'] = ip
            #dic['poc_prod'] = 'poc_prod'
            #dic['status'] = 'free'
            dic['Network'] = netSegment
        li.append(dic)
    endic = dict()
    endic['CIT_ipAddress'] = li
    print(json.dumps(endic))

if __name__ == '__main__':
    #设置传入参数
    parser = OptionParser()
    parser.add_option('--host', type=str, dest='host',default="192.168.1.0/24")
    #获取传入参数
    (options, args) = parser.parse_args()
    host = options.host
    ipy(host)