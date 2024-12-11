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

    def _sku_nat_gateway(self,subscriptionId):
        """
        Azure 资源NAT网关信息
        """
        api_version = '2021-08-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/'+ subscriptionId + '/providers/Microsoft.Network/natGateways?api-version=' + api_version
        return self.__retrieval_data(url)

    def _sku_vnetworks(self,subscriptionId):
        """
        Azure 资源网络信息
        """
        api_version = '2021-08-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/'+ subscriptionId + '/providers/Microsoft.Network/virtualNetworks?api-version=' + api_version
        return self.__retrieval_data(url)

    def _sku_vnetsubinfo(self,subscriptionId,resourceGroupName,virtualNetworkName):
        """
        Azure 资源虚拟网络子网信息
        """
        api_version = '2021-08-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/'+ subscriptionId + '/resourceGroups/' + resourceGroupName + '/providers/Microsoft.Network/virtualNetworks/' + virtualNetworkName + '/subnets?api-version=' + api_version
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
        # 获取订阅下所有NAT网关信息 
        natgeteways = self._sku_nat_gateway(subscriptionId)['value']
        # 获取订阅下所有虚拟网络信息 
        vnetworks = self._sku_vnetworks(subscriptionId)['value']
        # 获取订阅下资源组信息
        resourcegroups  = self._sku_resourcegroup(subscriptionId)['value']
        results = []
        for natgeteway in natgeteways:
            netgete = dict()
            netgete['id'] = natgeteway['id']  #NAT网关ID
            netgete['name'] = natgeteway['name']  #NAT网关名称
            resourceGroup = re.findall(r"(?<=resourceGroups\/).*?(?=\/providers)",natgeteway['id'])[0] #所属资源组
            for group in resourcegroups:
                if resourceGroup == group['name']:
                    netgete['resourceGroup'] = group['id']
                    break
            netgete['location'] = natgeteway['location']  #NAT网关区域
            netgete['status'] = natgeteway['properties']['provisioningState']  #NAT网关状态
            netgete['instanceId'] = [net['id'] for net in natgeteway['properties']['publicIpAddresses']][0]  #NAT网关绑定公网IP
            netgete['instanceId'] = [net['id'] for net in natgeteway['properties']['subnets']][0]  #NAT网关绑定子网ID
            vsubnet = [net['id'] for net in natgeteway['properties']['subnets']][0]  #NAT网关绑定子网ID
            for vnetwork in vnetworks:
                if vsubnet in [vnetsub['id'] for vnetsub in vnetwork['properties']['subnets']]:
                    netgete['vnetid'] = vnetwork['id']  # 网关所属虚拟网络ID
                    break
            netgete['valueMethod'] = '自动采集'
            netgete['dataStatus'] = '有效'
            netgete['cloudtype'] = 'Azure'
            netgete['valueMethodAdd'] = self.resource
            results.append(netgete)
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
    natnetlist = []
    for id in subscription_idlist:
        data = instance.retrieval(id)
        if data:
            natnetlist += data
    print(json.dumps({"CIT_NATGateway":natnetlist}, ensure_ascii=False, indent=2))