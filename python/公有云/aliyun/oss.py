# -*- coding: utf-8 -*-

import base64
import hmac
import requests
import sha
import xmltodict
import json
from datetime import datetime
from pyDes import *
from binascii import a2b_hex
from optparse import OptionParser
import dateutil.parser
import pytz

def des_decrypt(message):
    k = des('shsh', ECB, padmode=PAD_PKCS5)
    return k.decrypt(a2b_hex(message)).decode('utf8')

class OSS_GetInfo(object):
    def __init__(self,accesskey,accesskeysecret,endpoint):
        self.accesskey = accesskey
        self.accesskeysecret = accesskeysecret
        self.endpoint=endpoint

    def countSignature(self,bucket,object):
        '''
        计算请求头中所需要的签名
        '''
        GMT_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
        time = datetime.utcnow().strftime(GMT_FORMAT) #GMT时间
        if bucket != '':
            signature = hmac.new(self.accesskeysecret,
                                "GET\n\napplication/x-www-form-urlencoded\n"+time+"\n"+"/"+bucket+"/"+object,sha)
        else:
            signature = hmac.new(self.accesskeysecret,
                                "GET\n\napplication/xml\n"+time+"\n"+"/"+bucket,sha)
        Signature = base64.b64encode(signature.digest()) #计算出签名
        return time,Signature

    def ListBuckets(self):
        '''
        获取所有的bucket名称(ListBuckets)
        '''
        time,Signature = self.countSignature('','')
        url = "http://"+self.endpoint #请求的url
        header = {
            "Authorization" : "OSS "+self.accesskey+":"+Signature, 
            "Content-Type" : "application/xml",
            "Date" : time
        } #请求头
        info = requests.get(url=url,headers=header)#请求获取到xml格式的信息
        convertJson = xmltodict.parse(info.text, encoding = 'utf-8')
        jsonStr = json.dumps(convertJson, indent=1)#将获取到的xml格式的信息转成json格式
        bkDict = json.loads(jsonStr)#将json格式的数据loads一下,方便像字典那样取值
        allbkName = [str(bk.get('Name')) for bk in bkDict['ListAllMyBucketsResult']['Buckets']['Bucket']]
        return allbkName

    def getbucketInfo(self):
        '''
        获取bucket的相关信息(GetBucketInfo)
        '''
        allbk = self.ListBuckets()
        allbkli = []
        for bucket in allbk:
            object='?bucketInfo'
            time,Signature = self.countSignature(bucket,object)#返回请求的时间和计算签名
            url = "http://"+bucket+"."+self.endpoint+"/"+object # 请求的url
            header = {
                "Authorization" : "OSS "+self.accesskey+":"+Signature, 
                "Content-Type" : "application/x-www-form-urlencoded",
                "Date" : time
            } #请求头
            info = requests.get(url=url,headers=header)#请求获取数据

            convertJson = xmltodict.parse(info.text, encoding = 'utf-8')
            jsonStr = json.dumps(convertJson, indent=1)
            bkDict = json.loads(jsonStr)#将json格式的数据loads一下,方便像字典那样取值

            if bkDict['BucketInfo']['Bucket']['StorageClass'] == 'Standard':
                StorageClass = '标准存储'
            if bkDict['BucketInfo']['Bucket']['StorageClass'] == 'IA':
                StorageClass = '低频访问'
            if bkDict['BucketInfo']['Bucket']['StorageClass'] == 'Archive':
                StorageClass = '归档存储'
            if bkDict['BucketInfo']['Bucket']['StorageClass'] == 'ColdArchive':
                StorageClass = '冷归档存储'

            creatime =str(dateutil.parser.parse(bkDict['BucketInfo']['Bucket']['CreationDate']).astimezone(pytz.timezone('Asia/Shanghai')))
            createtime = datetime.strptime(creatime,"%Y-%m-%d %H:%M:%S+08:00").strftime("%Y-%m-%d")    #创建时间

            vkdic ={
                'CreationDate': createtime, #创建时间
                'CrossRegionReplication':str(bkDict['BucketInfo']['Bucket']['Location']), #区域
                'ExtranetEndpoint':str(bkDict['BucketInfo']['Bucket']['ExtranetEndpoint']), #外网域名
                'IntranetEndpoint':str(bkDict['BucketInfo']['Bucket']['IntranetEndpoint']), #内网域名
                'Name':str(bkDict['BucketInfo']['Bucket']['Name']), #名称
                'ID':str(bkDict['BucketInfo']['Bucket']['Name']),   #ID
                'StorageClass': StorageClass,   #类型
              	'cloudType':'AliYun',
                'valueMethod':'自动采集',    #来源方式,
                'dataStatus':'有效', #数据状态,
                'valueMethodAdd': 'https://oss-cn-shanghai.aliyuncs.com'   #数据采集地址
            }
            allbkli.append(vkdic)
        return allbkli

        
if __name__ == '__main__':
    #设置传入参数
    parser = OptionParser()
    parser.add_option('--accesskey', type=str, dest='accesskey')
    parser.add_option('--accesskeysecret', type=str, dest='accesskeysecret')
    parser.add_option('--endpoint', type=str,dest='endpoint', default='oss-cn-shanghai.aliyuncs.com')
    #获取传入参数
    (options, args) = parser.parse_args()
    accesskey = options.accesskey
    accesskeysecret = str(des_decrypt(options.accesskeysecret))
    endpoint = options.endpoint
    oss = OSS_GetInfo(accesskey,accesskeysecret,endpoint)
    bkinfo = oss.getbucketInfo()
    endic = dict()
    endic['CIT_ObjectStorageContainer'] = bkinfo
    print(json.dumps(endic,ensure_ascii=False))