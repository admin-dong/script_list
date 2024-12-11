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
from pyDes import *
from binascii import a2b_hex

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
access_key_secret = access_key_secret
server_address = 'https://vpc.aliyuncs.com/'
user_params = {'Action':'DescribeVSwitches','RegionId': zone } 
area_params = {'Action':'DescribeZones','RegionId': zone } 

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
    h = hmac.new(access_key_secret + "&", stringToSign, sha1)
    signature = base64.encodestring(h.digest()).strip()
    return signature




def region_url(area_params):
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time()))
    parameters = {
        'Format' : 'JSON',
        'Version': '2016-04-28',
        'AccessKeyId' : access_key_id,
        'SignatureVersion': '1.0',
        'SignatureMethod' : 'HMAC-SHA1',
        'SignatureNonce': str(uuid.uuid1()),
        'Timestamp' : timestamp
    }
    for key in area_params.keys():
        parameters[key] = area_params[key]
    signature = compute_signature(parameters, access_key_secret)
    parameters['Signature'] = signature
    area_url = server_address + "/?" + urllib.urlencode(parameters)
    return area_url




def compose_url(user_params):
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time()))
    parameters = {
        'Format' : 'JSON',
        'Version': '2016-04-28',
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

url = compose_url(user_params)
request = requests.get(url)
reques = json.dumps(request.json())
num = json.loads(reques).get('TotalCount')

area_url = region_url(area_params)
area_request = requests.get(area_url)
area_reques = json.dumps(area_request.json())
area_num = json.loads(area_reques).get('TotalCount')

page_nums = num/10
page_num = num%10
if page_num != 0 :
    page_nums += 1


VSwitche_list = []
for i in range(1,page_nums+1):

    area_user_paramss = {'Action':'DescribeZones','RegionId': zone,'PageNumber':str(i)}
    area_urll = region_url(area_user_paramss)
    area_requestt = requests.get(area_urll)
    area_requess = json.dumps(area_requestt.json())
    area_reqq = json.loads(area_requess)
    aliyun_area = area_reqq.get('Zones').get('Zone')

    user_paramss = {'Action':'DescribeVSwitches','RegionId': zone,'PageNumber':str(i)}
    urll = compose_url(user_paramss)
    requestt = requests.get(urll)
    requess = json.dumps(requestt.json())
    reqq = json.loads(requess)
    aliyun_VSwitches = reqq.get('VSwitches').get('VSwitch')

    for vswitche in aliyun_VSwitches:
        item = dict()
        item['VpcId'] = vswitche['VpcId']   #虚拟网络ID
        item['ID'] = vswitche['VSwitchId']  #虚拟子网ID
        item['VSwitchName'] = vswitche['VSwitchName']   #虚拟子网名称
        item['ResourceGroupId'] = vswitche['ResourceGroupId']   #资源组
        item['CidrBlock'] = vswitche['CidrBlock']   #IPV4网段
        item['Ipv6CidrBlock'] = vswitche['Ipv6CidrBlock']   #IPV6网段
        if vswitche['Status'] == 'Pending':
            item['Status'] = '配置中'
        if vswitche['Status'] == 'Available':
            item['Status'] = '可用'             
        item['cloudtype'] = 'AliYun'    #云类型
        item['Zone'] = vswitche['ZoneId']   #可用区
        item['valueMethod'] = '自动采集'    #来源方式
        item['dataStatus'] = '有效'
        item['valueMethodAdd'] = 'https://ecs.aliyuncs.com/'
        for area in aliyun_area:
            if item['Zone'] == area['ZoneId']:
                item['area'] = area['LocalName']
        VSwitche_list.append(item)

                

CIT_VirtualSubnet = dict()
CIT_VirtualSubnet['CIT_VirtualSubnet'] = VSwitche_list
print(json.dumps(CIT_VirtualSubnet,ensure_ascii=False))