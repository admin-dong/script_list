#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
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

    def _sku_vnetworks(self,subscriptionId):
        """
        Azure 资源网络信息
        """
        api_version = '2021-08-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/'+ subscriptionId + '/providers/Microsoft.Network/virtualNetworks?api-version=' + api_version
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
        vnetworks = self._sku_vnetworks(subscriptionId)['value']
        # print(networks)
        results = []
        subnetlist = []
        for vnetwork in vnetworks:
            # results.append(network)
            vnet = dict()
            vnet['id'] = vnetwork['id']  #虚拟网络ID
            vnet['name'] = vnetwork['name']  #虚拟网络名称
            vnet['resourceGroup'] = re.findall(r"(?<=resourceGroups\/).*?(?=\/providers)",vnetwork['id'])[0] #资源组
            try:
                vnet['networkSecurityGroup'] = [i['properties']['networkSecurityGroup']['id'] for i in vnetwork['properties']['subnets']][0]  #虚拟网络安全组
            except:
                pass
            vnet['ipaddress_scope'] = vnetwork['properties']['addressSpace']['addressPrefixes'][0]  #虚拟网络IP地址范围
            if vnetwork['properties']['provisioningState']  == "Updating": #虚拟子网状态
                vnet['status'] = "配置中"
            elif vnetwork['properties']['provisioningState']  == "Succeeded":
                vnet['status'] = "可用"
            vnet['location'] = vnetwork['location']  #区域

            vnet['valueMethod'] = '自动采集'
            vnet['dataStatus'] = '有效'
            vnet['cloudtype'] = 'Azure'
            vnet['valueMethodAdd'] = self.resource
            results.append(vnet)
            for vnetsub in vnetwork['properties']['subnets']:
                subnet = dict()
                subnet['subid'] = vnetsub['id']  #虚拟子网ID
                subnet['subname'] = vnetsub['name']  #虚拟子网名称
                subnet['resourceGroup'] = re.findall(r"(?<=resourceGroups\/).*?(?=\/providers)",vnetsub['id'])[0]  #资源组
                subnet['netid'] = vnetwork['id']  #虚拟子网所属网络ID
                subnet['subnetipaddress_scope'] = vnetsub['properties']['addressPrefix']  #虚拟子网IPv4网段
                if vnetsub['properties']['provisioningState']  == "Updating": #虚拟子网状态
                    subnet['status'] = "配置中"
                elif vnetsub['properties']['provisioningState']  == "Succeeded":
                    subnet['status'] = "可用"
                subnet['status'] = vnetsub['properties']['provisioningState']  #虚拟子网状态
                subnet['location'] = vnetwork['location']  #区域
                subnet['valueMethod'] = '自动采集'
                subnet['dataStatus'] = '有效'
                subnet['cloudtype'] = 'Azure'
                subnet['valueMethodAdd'] = self.resource
                subnetlist.append(subnet)
        if results != [] and subnetlist != []:
            return results,subnetlist

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
    vnetlist = []
    vnetsublist = []
    for id in subscription_idlist:
        data = instance.retrieval(id)
        if data:
            vnetlist += data[0]
            vnetsublist += data[1]
    print(json.dumps({"CIT_VirtualNetwork":vnetlist,"CIT_VirtualSubnet":vnetsublist}, ensure_ascii=False, indent=2))


