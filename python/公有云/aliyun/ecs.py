#!/usr/bin/env python
#coding: utf-8
#-*- encoding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
import urllib,urllib2
import base64
import hmac
import hashlib
from hashlib import sha1
import time
import uuid
import json
import requests
from optparse import OptionParser
import datetime
import dateutil.parser
from pyDes import *
from binascii import a2b_hex
import pytz

def des_decrypt(message):
    k = des('shsh', ECB, padmode=PAD_PKCS5)
    return k.decrypt(a2b_hex(message)).decode('utf8')

parser = OptionParser()
parser.add_option('--access_key_id', type=str, dest='access_key_id')
parser.add_option('--access_key_secret', type=str, dest='access_key_secret')
parser.add_option('--zone', type=str, dest='zone')
(options, args) = parser.parse_args()
access_key_id = options.access_key_id
access_key_secret = str(des_decrypt(options.access_key_secret))
zone = options.zone
access_key_id = access_key_id
# access_key_secret = options.access_key_secret
server_address = 'https://ecs.aliyuncs.com/'
user_params = {'Action':'DescribeInstances','RegionId': zone } 
disk_user_params = {'Action':'DescribeDisks','RegionId': zone } 

def percent_encode(encodeStr):
    encodeStr = str(encodeStr)
    res = urllib.quote(encodeStr.decode('utf8').encode('utf8'), '')
    res = res.replace('+', '%20')
    res = res.replace('*', '%2A')
    res = res.replace('%7E', '~')
    return res


def compute_signature(parameters, access_key_secret):
    sortedParameters = sorted(parameters.items(), key=lambda parameters: parameters[0])
    canonicalizedQueryString = ''
    for (k,v) in sortedParameters:
        canonicalizedQueryString += '&' + percent_encode(k) + '=' + percent_encode(v)
        stringToSign = 'GET&%2F&' + percent_encode(canonicalizedQueryString[1:])
    h = hmac.new(str(access_key_secret) + "&", str(stringToSign), sha1)
    signature = base64.encodestring(h.digest()).strip()
    return signature

def compose_url(user_params):
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time()))
    parameters = {
        'Format' : 'JSON',
        'Version': '2014-05-26',
        'AccessKeyId' : access_key_id,
        'SignatureVersion': '1.0',
        'SignatureMethod' : 'HMAC-SHA1',
        'SignatureNonce': str(uuid.uuid1()),
        'Timestamp' : timestamp
    }
    for key in user_params.keys():
        parameters[key] = user_params[key]
    signature = compute_signature(parameters, access_key_secret)
    parameters['Signature'] = signature
    url = server_address + "/?" + urllib.urlencode(parameters)
    return url
  
def disk_compose_url(disk_user_params):
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time()))
    parameters = {
        'Format' : 'JSON',
        'Version': '2014-05-26',
        'AccessKeyId' : access_key_id,
        'SignatureVersion': '1.0',
        'SignatureMethod' : 'HMAC-SHA1',
        'SignatureNonce': str(uuid.uuid1()),
        'Timestamp' : timestamp
    }
    for key in disk_user_params.keys():
        parameters[key] = disk_user_params[key]
    signature = compute_signature(parameters, access_key_secret)
    parameters['Signature'] = signature
    url = server_address + "/?" + urllib.urlencode(parameters)
    return url  

def disk_data():
    url = disk_compose_url(disk_user_params)
    request = requests.get(url)
    reques = json.dumps(request.json())
    num = json.loads(reques).get('TotalCount')
    page_nums = num/10
    page_num = num%10
    if page_num != 0 :
        page_nums += 1
    disk_list = []
    for i in range(1,page_nums+1):
        user_paramss = {'Action':'DescribeDisks','RegionId': zone,'PageNumber':str(i)}
        urll = disk_compose_url(user_paramss)
        requestt = requests.get(urll)
        requess = json.dumps(requestt.json())
        reqq = json.loads(requess)
        AliYun_disks = reqq.get('Disks').get('Disk')
        for disk in AliYun_disks:
            if disk.has_key('Attachments') == True:
                for i in disk['Attachments']['Attachment']:
                    InstanceId = i['InstanceId']  #云盘或本地盘挂载实例ID   
            Size = disk.get('Size')
            if disk.has_key('DiskName') == True:
                DiskName = disk.get('DiskName')
            if disk.get('Type'):
                if disk.get('Type') == 'system':
                    Type = '系统盘'
                if disk.get('Type') == 'data':
                    Type = '数据盘' 
            item = {
                'Ecs_ID':InstanceId,
                'Size':Size,
                'DiskName':DiskName,
                'Type':Type,
            }
            disk_list.append(item)
    return disk_list

  
  
url = compose_url(user_params)
request = requests.get(url)
reques = json.dumps(request.json())
num = json.loads(reques).get('TotalCount')
page_nums = num/10
page_num = num%10
if page_num != 0 :
    page_nums += 1
ecs_list = []

disk_all = disk_data()

for i in range(1,page_nums+1):
    user_paramss = {'Action':'DescribeInstances','RegionId': zone,'PageNumber':str(i)}
    urll = compose_url(user_paramss)
    requestt = requests.get(urll)
    requess = json.dumps(requestt.json())
    reqq = json.loads(requess)
    aliyun_ecs = reqq.get('Instances').get('Instance')
    for ecs in aliyun_ecs:
        Tag_list = list()
        if ecs['Tags']['Tag']:
            for tag in ecs['Tags']['Tag']:
                Tag_list.append(tag)
            for i in Tag_list:
                i["key"] = i.pop("TagKey")
                i["value"] = i.pop("TagValue")
        if ecs.get('InstanceName'):
            InstanceName = ecs.get('InstanceName')  #虚拟机名称
        if ecs.get('HostName'):
            HostName = ecs.get('HostName')  #主机名
        if ecs.get('Memory'):
            Memory = int(ecs.get('Memory'))/1024    #内存大小
        if ecs.get('InstanceId'):
            InstanceId = ecs.get('InstanceId')  #实例ID
        diskinfo = list()
        disk_list = []
        for disk in disk_all:
            if InstanceId == disk.get('Ecs_ID'):
                disk_list.append(disk.get('Size'))
                itsm = dict()
                itsm['diskSizeGB'] = disk.get('Size')
                itsm['diskName'] = disk.get('DiskName')
                itsm['diskType'] = disk.get('Type')
                diskinfo.append(itsm)
        if ecs.get('Cpu'):
            Cpu = ecs.get('Cpu')  #cpu数量
            
        if 'InstanceChargeType' in ecs.keys():
          if ecs.get('InstanceChargeType') == 'PrePaid':
            TayType = '包年包月'
          if ecs.get('InstanceChargeType') == 'PostPaid':
            TayType = '按量付费'
        if ecs.has_key('ResourceGroupId')==True:
            ResourceGroupId = ecs.get('ResourceGroupId')  #资源组id
        if ecs.get('RegionId'):
            RegionId = ecs.get('RegionId')  #地域id
        if ecs.get('ZoneId'):
            ZoneId = ecs.get('ZoneId')  #所属可用区
        if ecs.get('OSType'):
            OSType = ecs.get('OSType')  #操作系统类型
        if ecs.get('InstanceType'):
            InstanceType = ecs.get('InstanceType')  #规格
        if ecs.get('OSName'):
            OSName = ecs.get('OSName')  #操作系统名称
        if ecs.get('Status'):
            if ecs.get('Status') == 'Running':  
                Status = '开机' #实例状态
            else:
                Status = '关机' #实例状态
        if ecs['CreationTime']:
            catTime =str(dateutil.parser.parse(ecs['CreationTime']).astimezone(pytz.timezone('Asia/Shanghai')))
            CreationTime = datetime.datetime.strptime(catTime,"%Y-%m-%d %H:%M:%S+08:00").strftime("%Y-%m-%d")  
        if ecs.get('NetworkInterfaces'):
            for network in ecs['NetworkInterfaces']['NetworkInterface']:
                if network.get('PrimaryIpAddress'):
                    PrimaryIpAddress = network.get('PrimaryIpAddress')  #弹性网卡主私有IP地址
                for i in network['PrivateIpSets']['PrivateIpSet']:
                    if i['PrivateIpAddress']:
                        PrivateIpAddress = i['PrivateIpAddress']    #实例私网IP地址
        if ecs['VpcAttributes']['PrivateIpAddress']['IpAddress']:
            IpAddress =  ecs['VpcAttributes']['PrivateIpAddress']['IpAddress']   #私有IP地址
        item = {
            'InstanceName':InstanceName,
            'HostName':HostName,
            'Memory':Memory,
            'InstanceId':InstanceId,
            'diskinfo':diskinfo,
            'disk_size':sum(disk_list),
            'cpu':Cpu,
            'TayType':TayType,
            'ResourceGroupId':ResourceGroupId,
            'RegionId':RegionId,
            'ZoneId':ZoneId,
            'OSType':OSType,
            'InstanceType':InstanceType,
            'OSName':OSName,
            'Status':Status,
            'Tags':Tag_list,
            'vmDeleteTime':"",
            'PrimaryIpAddress':PrimaryIpAddress,
            'PrivateIpAddress':PrivateIpAddress,
            'IpAddress':IpAddress,
            'uuid': InstanceId,
            'area':'AliYun',
          	'CreationTime':CreationTime,
          	'recovery':'否',
            'valueMethod':'自动采集',
            'dataStatus':'有效',
            'valueMethodAdd':'https://ecs.aliyuncs.com/'
        }
        if ecs['PublicIpAddress']['IpAddress']:
            item['EIP'] = ecs['PublicIpAddress']['IpAddress'][0]
        if item.has_key('EIP') == True:
            item.get('IpAddress').append(item['EIP'])
        ecs_list.append(item)
CIT_VM = dict()
CIT_VM['CIT_VM'] = ecs_list
print(json.dumps(CIT_VM,ensure_ascii=False))