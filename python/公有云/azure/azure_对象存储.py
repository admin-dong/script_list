#!/usr/bin/python
# -*- coding: utf-8 -*-


import json
import uuid
import requests
import datetime
import hmac
import hashlib
import base64
import xmltodict
# from urllib.parse import urlencode #python3 使用
from urllib import urlencode #python2 使用
from optparse import OptionParser
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
        api_version = '1.0'
        token_url = 'https://login.chinacloudapi.cn/' + self.tenant_id + '/oauth2/token?api-version=' + api_version
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

    def __retrieval_data(self, url, ignore=False):
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
        if response.status_code != 200 and not ignore:
            raise Exception(json.dumps({
                'status': 'Failed',
                'msg': response.text
            }, ensure_ascii=False, indent=2))

        return response.json()

    def _subscriptions(self):
        api_version = '2020-01-01'
        url = self.resource + '/subscriptions?api-version=' + api_version
        subscriptions = self.__retrieval_data(url)

        return subscriptions.get('value') if subscriptions.get('value') else []

    def _storage_accounts(self,subscription_id,resource_group_name):
        """
        Azure 列举 资源组下 存储账号
        """
        api_version = '2021-04-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Storage/storageAccounts?api-version={apiVersion}'.format(subscriptionId=subscription_id,resourceGroupName=resource_group_name, apiVersion=api_version)
        storage_accounts = self.__retrieval_data(url)

        return storage_accounts.get('value') if storage_accounts.get('value') else []

    def _resource_groups(self, subscription_id):
        '''
        Azure 获取所有的资源组名称
        '''
        api_version = '2021-04-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/{subscriptionId}/resourcegroups?api-version={apiVersion}'.format(subscriptionId=subscription_id,apiVersion=api_version)
        resource_groups = self.__retrieval_data(url)
        return resource_groups.get('value') if resource_groups.get('value') else []

    def _blob_services(self, subscription_id, resource_group_name, account_name):
        api_version = '2021-09-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Storage/storageAccounts/{accountName}/blobServices?api-version={apiVersion}'.format(subscriptionId=subscription_id,resourceGroupName=resource_group_name,accountName=account_name, apiVersion=api_version)
        blob_services = self.__retrieval_data(url)

        return blob_services.get('value') if blob_services.get('value') else []

    def _containers(self, subscription_id, resource_group_name, account_name, blob_name):
        api_version = '2021-09-01'
        url = 'https://management.chinacloudapi.cn/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Storage/storageAccounts/{accountName}/blobServices/{blobName}/containers?api-version={apiVersion}'.format(subscriptionId=subscription_id,resourceGroupName=resource_group_name,accountName=account_name, blobName=blob_name, apiVersion=api_version)
        containers = self.__retrieval_data(url)
        return containers.get('value') if containers.get('value') else []

    def worker(self):
        # 获取全部订阅
        subscriptions = self._subscriptions()
        # 获取全部资源组
        results = []
        for subscription in subscriptions:
            # 获取订阅下资源组
            resource_groups = self._resource_groups(subscription.get('subscriptionId'))
            for resource_group in resource_groups:
                # 获取资源组下存储账户
                storage_accounts = self._storage_accounts(subscription.get('subscriptionId'), resource_group.get('name'))
                for account in storage_accounts:
                    # 获取存储账户下blob服务
                    blob_services = self._blob_services(subscription.get('subscriptionId'), resource_group.get('name'), account.get('name'))
                    for blob in blob_services:
                        # 获取blob服务下容器
                        containers = self._containers(subscription.get('subscriptionId'), resource_group.get('name'), account.get('name'), blob.get('name'))
                        for container in containers:
                            # 拼装数据实例
                            instance = {
                                'containerId': container.get('id'),
                                'containerName': container.get('name'),
                                'privateEndpoint': 'https://' + account.get('name') + '.blob.core.chinacloudapi.cn/',
                                'publicEndpoint': 'https://' + account.get('name') + '.blob.core.chinacloudapi.cn/',
                                'containerType': 'blob',
                                'accessTier': account['properties'].get('accessTier') if account.get('properties') else None,
                                'cloudType': 'Azure',
                                'location': account.get('location'),
                                'valueMethod': 'auto',
                                'dataStatus': 'efficient',
                                'valueMethodAdd': self.resource
                            }
                            results.append({k:v for k,v in instance.items() if v})

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
        client_secret=client_secret
    )
    print(json.dumps({"CIT_ObjectStorageContainer":instance.worker()}, ensure_ascii=False, indent=2))
