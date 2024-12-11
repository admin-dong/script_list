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
import pytz
#defaultencoding = 'utf-8'
#if sys.getdefaultencoding() != defaultencoding:
reload(sys)
sys.setdefaultencoding('utf-8')


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

    def _virtual_machine(self,subscriptionId):
        """
        Azure 列举 资源组下 虚拟主机基础信息
        """
        api_version = '2022-03-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/' + subscriptionId + '/providers/Microsoft.Compute/virtualMachines?api-version=' + api_version
        return self.__retrieval_data(url)

    def _virtual_status(self,subscriptionId):
        """
        Azure 列举 资源组下 虚拟主机状态
        """
        api_version = '2022-03-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/' + subscriptionId + '/providers/Microsoft.Compute/virtualMachines?api-version=' + api_version + '&statusOnly=true'
        return self.__retrieval_data(url)

    def _sku_specifications(self,subscriptionId):
        """
        Azure 资源SKU 规格信息
        """
        api_version = '2021-07-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/'+ subscriptionId + '/providers/Microsoft.Compute/skus?api-version=' + api_version
        return self.__retrieval_data(url)

    def _sku_images(self,subscriptionId):
        """
        Azure 资源映像信息
        """
        api_version = '2022-03-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/'+ subscriptionId + '/providers/Microsoft.Compute/images?api-version=' + api_version
        return self.__retrieval_data(url)

    def _sku_pubipaddress(self,subscriptionId):
        """
        Azure 资源公网IP信息
        """
        api_version = '2021-08-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/'+ subscriptionId + '/providers/Microsoft.Network/publicIPAddresses?api-version=' + api_version
        return self.__retrieval_data(url)

    def _sku_network(self,subscriptionId):
        """
        Azure 资源network信息
        """
        api_version = '2021-12-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/'+ subscriptionId + '/providers/Microsoft.Network/networkInterfaces?api-version=' + api_version
        return self.__retrieval_data(url)

    def _sku_networkgroup(self,subscriptionId):
        """
        Azure 资源vm network组信息
        """
        api_version = '2021-08-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/'+ subscriptionId + '/providers/Microsoft.Network/networkInterfaces?api-version=' + api_version
        return self.__retrieval_data(url)

    def _sku_disks(self,subscriptionId):
        """
        Azure 资源磁盘信息
        """
        api_version = '2021-12-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/'+ subscriptionId + '/providers/Microsoft.Compute/disks?api-version=' + api_version
        return self.__retrieval_data(url)

    def _sku_vm_publisherName(self,subscriptionId,publisherName):
        """
        Azure 资源虚拟机映像服务信息
        """
        api_version = '2022-03-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/'+ subscriptionId + '/providers/Microsoft.Compute/locations/'+ self.zone + '/publishers/' + publisherName + '/artifacttypes/vmimage/offers?api-version=2022-03-01'
        return self.__retrieval_data(url)

    def _sku_vm_images(self,subscriptionId,publisherName,offer,skus):
        """
        Azure 资源虚拟机映像信息
        """
        api_version = '2022-03-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/'+ subscriptionId + '/providers/Microsoft.Compute/locations/'+ self.zone + '/publishers/' + publisherName + '/artifacttypes/vmimage/offers/' + offer + '/skus/'+ skus + '/versions/?api-version=2022-03-01'
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


    def retrieval(self,subscriptionId):
        # 获取全部SKU规格，按照{区域:{SKU规格名称1：具体属性，SKU规格名称2：具体属性 ...}}格式作为map
        sku_spec = self._sku_specifications(subscriptionId)['value']
        # 获取订阅下所有映像信息
        # imagesa = self._sku_images()['value']
        # 获取订阅下所有磁盘信息 
        disks = self._sku_disks(subscriptionId)['value']
        # 获取订阅下所有虚拟机状态信息
        vmstatus = self._virtual_status(subscriptionId)['value']
        # 获取订阅下所有网络信息(包含私有ip和公网ip的id)
        network = self._sku_network(subscriptionId)['value']
        # 获取订阅下所有公网IP信息
        pubipaddress = self._sku_pubipaddress(subscriptionId)['value']
        specification_map = {item['name']:item for item in sku_spec}
        # 获取订阅下全部虚拟机实例
        virtual_machines = self._virtual_machine(subscriptionId)['value']
        # 获取订阅下资源组信息
        resourcegroups  = self._sku_resourcegroup(subscriptionId)['value']
        results = []
        for instance in virtual_machines:
            vm = dict()
            vm['instanceId'] = instance['properties']['vmId']
            resourceGroup = re.findall(r"(?<=resourceGroups\/).*?(?=\/providers)",instance['id'])[0]
            for group in resourcegroups:
                if resourceGroup == group['name']:
                    vm['resourceGroup'] = group['id']
                    break
            vm['uuid'] = str(instance['id'])
            vm['vhostname'] = instance['name']
            vm['location'] = instance['location']
            vm['spec'] = instance['properties']['hardwareProfile']['vmSize']
            disks_list = []
            if instance.get('properties').get('storageProfile').get('osDisk'):
                for disk in disks:
                    if instance.get('properties').get('storageProfile').get('osDisk').get('managedDisk').get('id') == disk['id']:
                        item = dict()
                        item['diskType'] = "系统盘"
                        item['diskName'] = disk['name']
                        item['diskSizeGB'] = disk['properties']['diskSizeGB']
                        disks_list.append(item)
                        break
            if instance.get('properties').get('storageProfile').get('dataDisks') != []:
                for dataid in [i['managedDisk']['id'] for i in instance.get('properties').get('storageProfile').get('dataDisks')]:
                    for disk in disks:
                        if dataid == disk['id']:
                            item = dict()
                            item['diskType'] = "数据盘"
                            item['diskName'] = disk['name']
                            item['diskSizeGB'] = disk['properties']['diskSizeGB']
                            disks_list.append(item)
                            break
            vm['diskinfo'] = disks_list
            if instance.get('tags'):
                tags = []
                for k,v in instance.get('tags').iteritems():
                    tag = dict()
                    tag['key'] = k
                    tag['value'] = v
                    tags.append(tag)
                    # tags.append('{}={}'.format(k,v))
                vm['tags'] = tags
            if instance.get('properties').get('storageProfile').get('imageReference'):
                vm['ostype'] = instance['properties']['storageProfile']['imageReference']['offer']
                vm['osversion'] = instance['properties']['storageProfile']['imageReference']['exactVersion']
            #获取虚拟机状态，更新至vm实例
            for vstatus in vmstatus:
                if vstatus['properties']['vmId'] == instance['properties']['vmId']:
                    if "running" in vstatus['properties']['instanceView']['statuses'][1]['displayStatus']:
                        vm['status'] = "PowerOn"
                    if "stopped" in vstatus['properties']['instanceView']['statuses'][1]['displayStatus']:
                        vm['status'] = "PowerOff"
            #获取虚拟机ip，更新至vm实例
            iplist= []
            for net in network:
                if net.get('properties').get('virtualMachine') and net['properties']['virtualMachine']['id'].lower() == instance['id'].lower():
                    iplist += [ips['properties']['privateIPAddress'] for ips in net['properties']['ipConfigurations']]
                    for pubip in pubipaddress:
                        try:
                            if pubip['id'] in [ips['properties']['publicIPAddress']['id'] for ips in net['properties']['ipConfigurations']]:
                                iplist.append(pubip['properties']['ipAddress'])
                        except:
                            continue
            vm['iplist'] = iplist
            # 获取虚拟机规格信息，更新至vm实例
            instance_spec = specification_map.get(instance['properties']['hardwareProfile']['vmSize'])
            vm.update({item['name']:item['value'] for item in instance_spec['capabilities'] if item['name'] in ['vCPUs', 'MemoryGB'] })
            # 计算总磁盘大小，更新至vm实例
            os_disk_size_gb = instance['properties']['storageProfile']['osDisk']['diskSizeGB']
            data_disk_size_gb = 0
            for disk in instance['properties']['storageProfile']['dataDisks']:
                data_disk_size_gb += disk['diskSizeGB']
            vm.update({'totalDiskGb': os_disk_size_gb + data_disk_size_gb})
            vm['vmDeleteTime'] = ""
            vm['valueMethod'] = 'auto'
            vm['dataStatus'] = 'efficient'
            vm['datacenter'] = 'Azure'
            vm['recovery'] = 'False'
            vm['valueMethodAdd'] = self.resource
            results.append(vm)
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
    client_secret = des_decrypt(options.client_secret)
    # client_secret = options.client_secret
    instance = RetrievalInstance(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )
    subscription_idlist = [idlist['subscriptionId']for idlist in instance._sku_subscription()['value']]
    vmlist = []
    for id in subscription_idlist:
        data = instance.retrieval(id)
        if data:
            vmlist += data
    print(json.dumps({"CIT_VM":vmlist}, ensure_ascii=False, indent=2))
