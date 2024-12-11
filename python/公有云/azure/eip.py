#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import requests
from itertools import groupby
from operator import itemgetter
from urllib import urlencode
from optparse import OptionParser
import sys
import re
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
    def __init__(self, tenant_id , client_id, client_secret):
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


    
    def _sku_Public(self,subscriptionId):
        api_version = '2021-08-01'
        # url= 'https://management.chinacloudapi.cn/subscriptions/939105c6-5ae0-49d0-95e8-9af465630069/resourceGroups/NGBOH-RG/providers/Microsoft.Network/networkInterfaces/ngboh07438/ipConfigurations/ipconfig1?api-version=2021-08-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/'+ subscriptionId + '/providers/Microsoft.Network/publicIPAddresses?api-version={}'.format(api_version)
        return self.__retrieval_data(url)
    
    def _sku_Public_config(self,ipconfigid):
        api_version = '2021-08-01'
        url = 'https://management.chinacloudapi.cn'+ ipconfigid + '?api-version={}'.format(api_version)
        return self.__retrieval_data(url)

    def _sku_resourcegroup(self,subscriptionId):
        """
        Azure 订阅下资源组信息
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


    def retrieval(self,subscriptionId):
        Publics =  self._sku_Public(subscriptionId)['value']
        # 获取订阅下资源组信息
        resourcegroups  = self._sku_resourcegroup(subscriptionId)['value']
        results = list()
        for public in Publics:
            item = dict()
            item['id'] = public['id']   #公网IP ID
            item['name'] = public['name']   #公网IP名称
            item['location'] = public['location']   #区域
            if 'ipAddress' in public['properties'].keys():
                item['ipAddress'] = public['properties']['ipAddress']   #IP地址
            else:
                pass
                #ipconfigid = public['properties']['ipConfiguration']['id']
                #item['ipAddress'] = self._sku_Public_config(ipconfigid)['properties']['privateIPAddress']
            resourceGroup = re.findall(r"(?<=resourceGroups\/).*?(?=\/providers)",public['id'])[0]
            for group in resourcegroups:
                if resourceGroup == group['name']:
                    item['resourceGroup'] = group['id']
                    break
            if 'tags' in public.keys():
                Tag_list = list()
                for k,v in public.get('tags').items():
                    Tag_dict = dict()
                    Tag_dict['key'] = k
                    Tag_dict['value'] = v
                    Tag_list.append(Tag_dict)
                item['tags'] = Tag_list
            else:
                pass
            if 'id' in public['properties']['ipConfiguration'].keys():
                NATID = public['properties']['ipConfiguration']['id'] 
                NID = NATID.split('/ipConfigurations/ipconfig1')[0]
                item['ipConfiguration'] =NID #网卡ID
                item['bindType'] = '网卡信息'   #绑定实例类型
                item['bindState'] = '已绑定'    #绑定状态
            else:
                item['bindState'] = '未分配'
            item['cloudType'] = 'Azure' #云类型
            item['valueMethod'] = '自动采集'    #来源方式
            item['dataStatus'] = '有效' #数据状态   
            item['valueMethodAdd'] = self.resource  #数据采集地址
            results.append(item)
        if results != []:
            return  results        
            


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
    publicsiplist = []
    for id in subscription_idlist:
        data = instance.retrieval(id)
        if data:
            publicsiplist += data
    print(json.dumps({"CIT_PublicIP":publicsiplist}, ensure_ascii=False)) 