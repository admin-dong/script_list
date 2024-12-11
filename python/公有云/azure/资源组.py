#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import requests
import re
from itertools import groupby
from operator import itemgetter
from urllib import urlencode
from optparse import OptionParser
import sys
from pyDes import *
from binascii import a2b_hex
defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)
def des_decrypt(message):
    k = des('shsh', ECB, padmode=PAD_PKCS5)
    return k.decrypt(a2b_hex(message)).decode('utf8')

class RetrievalInstance(object):
    def __init__(self, tenant_id, client_id, client_secret):
        self.resource = 'https://management.chinacloudapi.cn' # Azure 中国区
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = self._access_token()

    def _access_token(self):
        """
        获取Azure 检索所需认证Token
        """
        token_url = 'https://login.chinacloudapi.cn/' + self.tenant_id + '/oauth2/token?api-version=1.0'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        body = {
            'grant_type': 'client_credentials',
            'resource': self.resource,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        response = requests.post(
            url=token_url,
            data=urlencode(body),
            headers=headers
        )
        access_token = json.loads(response.text).get('access_token')
        return access_token

    def _sku_subscription(self):
        """
        Azure subscription ID列表
        """
        api_version = '2020-01-01'
        url = 'https://management.chinacloudapi.cn/subscriptions?api-version=' + api_version
        return self.__retrieval_data(url)

    def _sku_resourcegroup(self,subscriptionId):
        """
        Azure 资源资源组信息
        """
        api_version = '2021-04-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/'+ subscriptionId + '/resourcegroups?api-version=' + api_version
        return self.__retrieval_data(url)

    def __retrieval_data(self, url):
        """
        检索数据 basic function
        """
        headers = {
            'Authorization': 'Bearer ' + self.token,
            'Content-Type': 'application/json'
        }
        response = requests.get(
            url=url,
            headers=headers
        )
        if response.status_code != 200:
            raise Exception(json.dumps({
                'status': 'Failed',
                'msg': response.text
            }, ensure_ascii=False, indent=2))
        # return response.json().get('value')
        return response.json()


    def retrieval(self,subscriptionId,subscriptionname):
        # 获取订阅下所有资源组信息 
        grouplist = self._sku_resourcegroup(subscriptionId)['value']
        results = []
        for groups in grouplist:
            group = dict()
            group['id'] = groups['id']  #资源组ID
            group['name'] = groups['name']  #资源组名称
            group['subid'] = subscriptionId  #资源组所属订阅ID
            group['subname'] = subscriptionname  #资源组所属订阅名称
            group['location'] = groups['location']   #区域
            group['status'] = groups['properties']['provisioningState']  #资源组状态
            if groups.get('tags') and groups.get('tags') != {}:
                tags = []
                for k,v in groups.get('tags').iteritems():
                    tag = dict()
                    tag['key'] = k
                    tag['value'] = v
                    tags.append(tag)
                group['tags'] = tags
            group['valueMethod'] = '自动采集'
            group['dataStatus'] = '有效'
            group['cloudtype'] = 'Azure'
            group['valueMethodAdd'] = self.resource
            results.append(group)
        if results and results != []:
            return results

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--tenant_id', type=str, dest='tenant_id')
    parser.add_option('--client_id', type=str, dest='client_id')
    parser.add_option('--client_secret', type=str, dest='client_secret')
    (options, args) = parser.parse_args()
    tenant_id = options.tenant_id
    client_id = options.client_id
    # client_secret = options.client_secret
    client_secret = des_decrypt(options.client_secret)
    instance = RetrievalInstance(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )
    disklist = []
    for i in instance._sku_subscription()['value']:
        data = instance.retrieval(i['subscriptionId'],i['displayName'])
        if data:
            disklist += data
    print(json.dumps({"CIT_resourceGroup":disklist}, ensure_ascii=False, indent=2))
