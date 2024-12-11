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

    def _sku_elbs(self,subscriptionId):
        """
        Azure 资源负载均衡信息
        """
        api_version = '2021-08-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/'+ subscriptionId + '/providers/Microsoft.Network/loadBalancers?api-version=' + api_version
        return self.__retrieval_data(url)

    def _sku_elblisten(self,subscriptionId,resourceGroupName,loadBalancerName):
        """
        Azure 资源负载均衡监听器信息
        """
        api_version = '2021-08-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/'+ subscriptionId + '/resourceGroups/' + resourceGroupName +  '/providers/Microsoft.Network/loadBalancers/' + loadBalancerName + '/probes?api-version=' + api_version
        return self.__retrieval_data(url)

    def _sku_elbipaddress(self,subscriptionId,resourceGroupName,loadBalancerName):
        """
        Azure 资源负载均衡后端地址池信息
        """
        api_version = '2021-08-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/'+ subscriptionId + '/resourceGroups/' + resourceGroupName +  '/providers/Microsoft.Network/loadBalancers/' + loadBalancerName + '/backendAddressPools?api-version=' + api_version
        return self.__retrieval_data(url)

    def _sku_elbnetinfo(self,subscriptionId,resourceGroupName):
        """
        Azure 指定资源组下的网络接口信息
        """
        api_version = '2021-08-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/'+ subscriptionId + '/resourceGroups/' + resourceGroupName +  '/providers/Microsoft.Network/networkInterfaces?api-version=' + api_version
        return self.__retrieval_data(url)

    def _sku_elbnetwork(self,subscriptionId):
        """
        Azure 指定资源组下的虚拟网络信息
        """
        api_version = '2021-08-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/' + subscriptionId + '/providers/Microsoft.Network/virtualNetworks?api-version=' + api_version
        return self.__retrieval_data(url)

    def _virtual_machine(self,subscriptionId,resourceGroupName):
        """
        Azure 列举 资源组下 虚拟主机基础信息
        """
        api_version = '2022-03-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/' + subscriptionId + '/resourceGroups/' + resourceGroupName + '/providers/Microsoft.Compute/virtualMachines?api-version=' + api_version
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
        # 获取订阅下所有负载均衡信息
        elbs = self._sku_elbs(subscriptionId)['value']
        # 获取订阅下资源组信息
        resourcegroups  = self._sku_resourcegroup(subscriptionId)['value']
        results = []
        listen_list = []
        for elb in elbs:
            elbdict = dict()
            elbdict['elbid'] = elb['id']   #负载均衡ID
            elbdict['name'] = elb['name']   #负载均衡name
            resourceGroupName = re.findall(r"(?<=resourceGroups\/).*?(?=\/providers)",elb['id'])[0] #资源组
            for group in resourcegroups:
                if resourceGroupName == group['name']:
                    elbdict['resourceGroup'] = group['id']
                    break
            elbdict['location'] = elb['location']  #区域
            elbdict['status'] = elb['properties']['provisioningState']  #状态
            elbdict['ipaddress'] = [i['properties']['privateIPAddress'] for i in elb['properties']['frontendIPConfigurations']][0] #负载均衡服务地址
            try:
                elbdict['pubipaddress'] = [i['properties']['privateIPAddress'] for i in elb['properties']['frontendIPConfigurations']][1] #负载均衡服务地址
            except:
                pass
            vmdatas = self._virtual_machine(subscriptionId,resourceGroupName)['value']
            elbdict['listens'] = [lists['name'] for lists in elb['properties']['probes']]   #负载均衡监听器列表
            groupnetinfo = self._sku_elbnetinfo(subscriptionId,resourceGroupName)['value']
            netidlist = [net['id'] for net in [nets['properties']['backendIPConfigurations'] for nets in elb['properties']['backendAddressPools']][0]] #负载均衡网络id列表
            netid = [net['id'] for net in [nets['properties']['backendIPConfigurations'] for nets in elb['properties']['backendAddressPools']][0]][0]
            for listen in elb['properties']['loadBalancingRules']:
                listendict = dict()
                listendict['listenid'] = listen['id']  #监听器id
                listendict['listenname'] = listen['name']  #监听器名称
                listendict['elbid'] = elb['id']  #负载均衡id
                listendict['protocol'] = listen['properties']['protocol']  #监听器协议
                listendict['port'] = listen['properties']['backendPort']  #监听器端口
                listendict['location'] = elb['location']  #区域
                backendAddressPool = listen['properties']['backendAddressPool']['id']
                serverlist = []
                for pool in elb['properties']['backendAddressPools']:
                    if backendAddressPool == pool['id']:
                        for gnetinfo in groupnetinfo:
                            server= dict()
                            vmid = gnetinfo['properties']['virtualMachine']['id']
                            for vmdata in vmdatas:
                                if vmid.lower() == vmdata['id'].lower():
                                    server['name'] = vmdata['name']
                                    if vmdata['tags']:
                                        server['tags'] = vmdata['tags']
                            for netinfos in gnetinfo['properties']['ipConfigurations']:
                                if netinfos['id'] in netidlist:
                                    server['IP'] = netinfos['properties']['privateIPAddress']
                                    server['port'] = listen['properties']['backendPort']
                                    server['protocol'] = listen['properties']['protocol']
                            serverlist.append(server)
                listendict['serverlist'] = serverlist
                listendict['valueMethod'] = '自动采集'
                listendict['dataStatus'] = '有效'
                listendict['cloudtype'] = 'Azure'
                listendict['valueMethodAdd'] = self.resource
                listen_list.append(listendict)
            groupnetwork = self._sku_elbnetwork(subscriptionId)['value']
            server_list = []
            if groupnetwork and groupnetwork != "null":
                for gnetwork in groupnetwork:
                    if netid in [netid['id'] for netid in  [i['properties']['ipConfigurations'] for i in gnetwork['properties']['subnets']][0]]:
                        elbdict['networkid'] = gnetwork['id']
                        break
            elbdict['valueMethod'] = '自动采集'
            elbdict['dataStatus'] = '有效'
            elbdict['cloudtype'] = 'Azure'
            elbdict['valueMethodAdd'] = self.resource
            if elb.get('tags') and elb.get('tags') != {}:
                tags = []
                for k,v in elb.get('tags').iteritems():
                    tag = dict()
                    tag['key'] = k
                    tag['value'] = v
                    tags.append(tag)
                elbdict['tags'] = tags
            results.append(elbdict)
        if results != [] and listen_list != []:
            return results,listen_list

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
    elblist = []
    elblisten = []
    for id in subscription_idlist:
        data = instance.retrieval(id)
        if data:
            elblist += data[0]
            elblisten += data[1]
    print(json.dumps({"CIT_LoadBalancer":elblist,"CIT_LoadBalanceListener":elblisten}, ensure_ascii=False, indent=2))