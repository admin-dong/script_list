#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@FileName    :azurevnetinfo.py
@Describe    :
@DateTime    :2022/07/09 16:48:33
@Author      :douqing
'''
import json
import requests
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

    def _sku_vnetinfo(self,subscriptionId):
        """
        Azure 资源网络接口信息
        """
        api_version = '2021-08-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/'+ subscriptionId + '/providers/Microsoft.Network/networkInterfaces?api-version=' + api_version
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
        # 获取订阅下所有虚拟网卡信息 
        vnetinfos = self._sku_vnetinfo(subscriptionId)['value']
        results = []
        for vnetinfo in vnetinfos:
            netinfo = dict()
            netinfo['id'] = vnetinfo['id']  #网卡ID
            netinfo['name'] = vnetinfo['name']  #网卡名称
            netinfo['location'] = vnetinfo['location']  #区域
            try:
                netinfo['vmid'] = vnetinfo['properties']['virtualMachine']['id']  #网卡虚机标识
            except:
                pass
            try:
                netinfo['macAddress'] = vnetinfo['properties']['macAddress']  #网卡mac地址
            except:
                pass
            netinfo['subnetid'] = [vinfo['properties']['subnet']['id'] for vinfo in vnetinfo['properties']['ipConfigurations']][0]  #网卡所属虚拟子网
            netinfo['ipaddress'] = [vinfo['properties']['privateIPAddress'] for vinfo in vnetinfo['properties']['ipConfigurations']][0]  #网卡私网IP
            netinfo['privateIPAllocationMethod'] = [vinfo['properties']['privateIPAllocationMethod'] for vinfo in vnetinfo['properties']['ipConfigurations']][0]  #网卡IP分配方式
            if [vinfo['properties']['privateIPAllocationMethod'] for vinfo in vnetinfo['properties']['ipConfigurations']][0] == "Dynamic":
                netinfo['privateIPAllocationMethod'] = "动态"
            elif [vinfo['properties']['privateIPAllocationMethod'] for vinfo in vnetinfo['properties']['ipConfigurations']][0] == "Static":
                netinfo['privateIPAllocationMethod'] = "静态"
            netinfo['valueMethod'] = '自动采集'
            netinfo['dataStatus'] = '有效'
            netinfo['cloudtype'] = 'Azure'
            netinfo['valueMethodAdd'] = self.resource
            results.append(netinfo)
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
    vnetinfolist = []
    for id in subscription_idlist:
        data = instance.retrieval(id)
        if data:
            vnetinfolist += data
    print(json.dumps({"CIT_VirtualNetworkInterfaceCard":vnetinfolist}, ensure_ascii=False, indent=2))


