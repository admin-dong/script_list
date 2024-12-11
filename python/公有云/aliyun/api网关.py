#!/usr/bin/env python
#coding: utf-8
#-*- encoding:utf-8 -*-

from errno import EPIPE
from pkgutil import iter_modules
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
import pytz
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
server_address = 'https://apigateway.{}.aliyuncs.com/'.format(zone)
user_params = {'Action':'DescribeInstances','RegionId': zone } 

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
        'Version': '2016-07-14',
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
gateway_list = []
for i in range(1,page_nums+1):
    user_paramss = {'Action':'DescribeInstances','RegionId': zone,'PageNumber':str(i)}
    urll = compose_url(user_paramss)
    requestt = requests.get(urll)
    requess = json.dumps(requestt.json())
    reqq = json.loads(requess)
    aliyun_apigateway = reqq.get('Instances').get('InstanceAttribute')
    for api in aliyun_apigateway:
        item = dict()
        if api['InstanceId']:
            item['ID'] = api['InstanceId']  #ID
        if api['InstanceName']:
            item['Name'] = api['InstanceName']  #名称
        if api['InstanceRpsLimit']:
            item['InstanceRpsLimit'] = api['InstanceRpsLimit']  #rps限制数
        if api['VpcEgressAddress']:
            item['VpcEgressAddress'] = api['VpcEgressAddress'].split(',')  #内网VPC出口网段
        if api['InternetEgressAddress']:
            item['InternetEgressAddress'] = api['InternetEgressAddress'].split(',')    #公网出口地址
        if api.has_key('ZoneLocalName') == True:
            item['ZoneLocalName'] = api['ZoneLocalName']    #区域
        if api.has_key('ZoneId') == True:
            item['ZoneId'] = api['ZoneId']  #可用区
        item['cloudType'] = 'AliYun'
        item['valueMethod'] = '自动采集'
        item['dataStatus'] = '有效'
        item['valueMethodAdd'] = server_address
        gateway_list.append(item)

CIT_APIGateway = dict()
CIT_APIGateway['CIT_APIGateway'] = gateway_list
print(json.dumps(CIT_APIGateway,ensure_ascii=False))