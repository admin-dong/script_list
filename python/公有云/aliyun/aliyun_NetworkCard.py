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
server_address = 'https://ecs.aliyuncs.com/'
user_params = {'Action':'DescribeNetworkInterfaces','RegionId': zone } 
area_address = 'https://vpc.aliyuncs.com/'
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
    area_url = area_address + "/?" + urllib.urlencode(parameters)
    return area_url


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


eni_list = []
for i in range(1,page_nums+1):

    area_user_paramss = {'Action':'DescribeZones','RegionId': zone,'PageNumber':str(i)}
    area_urll = region_url(area_user_paramss)
    area_requestt = requests.get(area_urll)
    area_requess = json.dumps(area_requestt.json())
    area_reqq = json.loads(area_requess)
    aliyun_area = area_reqq.get('Zones').get('Zone')

    user_paramss = {'Action':'DescribeNetworkInterfaces','RegionId': zone,'PageNumber':str(i)}
    urll = compose_url(user_paramss)
    requestt = requests.get(urll)
    requess = json.dumps(requestt.json())
    reqq = json.loads(requess)
    aliyun_eni = reqq.get('NetworkInterfaceSets').get('NetworkInterfaceSet')

    for eni in aliyun_eni:
        item = dict()
        item['ID'] = eni['NetworkInterfaceId']  #ID
        if eni.has_key('NetworkInterfaceName') == True:
            item['name'] = eni['NetworkInterfaceName']  #网卡名称
        item['InstanceId'] = eni['InstanceId']  #虚拟标识
        item['VSwitchId'] = eni['VSwitchId']    #虚拟交换机ID
        item['PrivateIpAddress'] = eni['PrivateIpAddress']  #私网IP
        item['MacAddress'] = eni['MacAddress']  #MAC地址
        item['Zone'] = eni['ZoneId']  #可用区
        item['valueMethod'] = '自动采集'
        item['dataStatus'] = '有效'
        item['cloud_type'] = 'AliYun'
        item['valueMethodAdd'] = 'https://ecs.aliyuncs.com/'
        for area in aliyun_area:
            if item['Zone'] == area['ZoneId']:
                item['area'] = area['LocalName']
        eni_list.append(item)

CIT_VirtualNetworkInterfaceCard = dict()
CIT_VirtualNetworkInterfaceCard['CIT_VirtualNetworkInterfaceCard'] = eni_list
print(json.dumps(CIT_VirtualNetworkInterfaceCard,ensure_ascii=False))
