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
user_params = {'Action':'DescribeNatGateways','RegionId': zone } 

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
   # print ("stringToSign:"+stringToSign)
    h = hmac.new(access_key_secret + "&", stringToSign, sha1)
    signature = base64.encodestring(h.digest()).strip()
   # print(signature)
    return signature

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
page_nums = num/10
page_num = num%10
if page_num != 0 :
    page_nums += 1
NAT_list = []
for i in range(1,page_nums+1):
    user_paramss = {'Action':'DescribeNatGateways','RegionId': zone,'PageNumber':str(i)}
    urll = compose_url(user_paramss)
    requestt = requests.get(urll)
    requess = json.dumps(requestt.json())
    reqq = json.loads(requess)
    aliyun_NAT = reqq.get('NatGateways').get('NatGateway')
    for NAT in aliyun_NAT:
        item = dict()
        if NAT['Status']:
            if NAT['Status'] == 'Creating':
                item['Status'] = '创建中'
            if NAT['Status'] == 'Available':
                item['Status'] = '可用'
            if NAT['Status'] == 'Modifying':
                item['Status'] = '修改中'
            if NAT['Status'] == 'Deleting':
                item['Status'] = '删除中'
            if NAT['Status'] == 'Converting':
                item['Status'] = '转换中'
        if NAT['VpcId']:
            item['VpcId'] = NAT['VpcId'] #NAT网关所属VPC的ID
        if NAT['RegionId']:
            item['RegionId'] = NAT['RegionId']  #区域
        if NAT['ResourceGroupId']:
            item['ResourceGroupId'] = NAT['ResourceGroupId'] #资源组ID
        if NAT['NatGatewayId']:
            item['NatGatewayId'] = NAT['NatGatewayId']  #NAT网关ID
        # if NAT['BusinessStatus']:
        #     if NAT['BusinessStatus'] == 'Normal':
        #         item['InternetChargeType'] = '正常'     #NAT网关业务状态
        #     if NAT['BusinessStatus'] == 'FinancialLocked':
        #         item['InternetChargeType'] = '欠费锁定状态'     #NAT网关业务状态
        if NAT['Name']:
            item['Name'] = NAT['Name']  #NAT网关实例名称
        if NAT['IpLists']:
            EipID=list()
            for ip in NAT['IpLists']['IpList']:
                EipID.append(ip['AllocationId'])    #公网IP地址
            item['EipID'] = EipID
        if NAT['NatGatewayPrivateInfo']['IzNo']:
            item['IzNo'] = NAT['NatGatewayPrivateInfo']['IzNo']     #NAT网关可用区
        if NAT['NatGatewayPrivateInfo']['VswitchId']:
            item['VswitchId'] = NAT['NatGatewayPrivateInfo']['VswitchId']   #子网实例
        item['cloud_type'] = 'AliYun'
        item['valueMethod'] = '自动采集'
        item['dataStatus'] = '有效'
        item['valueMethodAdd'] = 'https://vpc.aliyuncs.com/'
        NAT_list.append(item)

CIT_NATGateway = dict()
CIT_NATGateway['CIT_NATGateway'] = NAT_list
print(json.dumps(CIT_NATGateway,ensure_ascii=False))

