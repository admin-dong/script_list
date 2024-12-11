#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import requests
from itertools import groupby
from operator import itemgetter
# from urllib2.parse import urlencode
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

    def _sku_disks(self,subscriptionId):
        """
        Azure 资源磁盘信息
        """
        api_version = '2021-12-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/'+ subscriptionId + '/providers/Microsoft.Compute/disks?api-version=' + api_version
        return self.__retrieval_data(url)

    def _virtual_machine(self,subscriptionId):
        """
        Azure 列举 订阅下 虚拟主机基础信息
        """
        api_version = '2022-03-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/' + subscriptionId + '/providers/Microsoft.Compute/virtualMachines?api-version=' + api_version
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


    def retrieval(self,subscriptionId):
        # 获取订阅下所有磁盘信息 
        disks = self._sku_disks(subscriptionId)['value']
        virtual_machines = self._virtual_machine(subscriptionId)['value']
        results = []
        for disk in disks:
            dis = dict()
            dis['instanceId'] = disk['id']
            dis['name'] = disk['name']
            if disk.get('managedBy'):
                dis['managedBy'] = disk['managedBy']
                for vm in virtual_machines:
                    if disk['id'] == vm['properties']['storageProfile']['osDisk']['managedDisk']['id']:
                        dis['managedBy'] = vm['id']
                        dis['disk_type'] = "系统盘"
                    if disk['id'] in [dname['managedDisk']['id'] for dname in vm['properties']['storageProfile']['dataDisks']]:
                        dis['managedBy'] = vm['id']
                        dis['disk_type'] = "数据盘"
                        # if disk['name'] == vm['properties']['storageProfile']['osDisk']['name']:
                        #     dis['disk_type'] = "系统盘"
                        # if disk['name'] in [dname['name'] for dname in vm['properties']['storageProfile']['dataDisks']]:
                        #     dis['disk_type'] = "数据盘"
            dis['location'] = disk['location']
            dis['diskSizeGB'] = disk['properties']['diskSizeGB']
            if  disk['properties']['diskState'] == "Attached":
                dis['status'] = "已绑定"
            elif  disk['properties']['diskState'] == "Unattached":
                dis['status'] = "未绑定"
            dis['valueMethod'] = '自动采集'
            dis['dataStatus'] = '有效'
            dis['cloudtype'] = 'Azure'
            dis['valueMethodAdd'] = self.resource
            if disk.get('tags') and disk.get('tags') != {}:
                tags = []
                for k,v in disk.get('tags').iteritems():
                    tag = dict()
                    tag['key'] = k
                    tag['value'] = v
                    tags.append(tag)
                dis['tags'] = tags
            results.append(dis)
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
    subscription_idlist = [idlist['subscriptionId']for idlist in instance._sku_subscription()['value']]
    disklist = []
    for id in subscription_idlist:
        data = instance.retrieval(id)
        if data:
            disklist += data
    print(json.dumps({"CIT_EVS":disklist}, ensure_ascii=False, indent=2))