
#!/usr/bin/python
# -*- coding: utf-8-*-

import json
import requests
from pyDes import *
from optparse import OptionParser
from binascii import a2b_hex




def des_decrypt(message):
    k = des('sdadadsa', ECB, padmode=PAD_PKCS5)
    return k.decrypt(a2b_hex(message)).decode('utf8')


class getNacosInfo():
    def __init__(self,clientUrl,nacosUsername,nacosPasswrod):
        self.clientUrl = clientUrl
        self.nacosUsername = nacosUsername
        self.nacosPasswrod = nacosPasswrod
        self.nacos_login_data = {
            "username": self.nacosUsername,
            "password": self.nacosPasswrod
        }
        self.token = self.nacosLogin()
    
    def nacosLogin(self):
        loginUrl = 'http://'+self.clientUrl +':8848/nacos/v1/auth/users/login'
        """
        登陆nacos,获取token
        :param env_url: 环境域名
        :return: nacos token
        """
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        response = requests.post(url=loginUrl, headers=headers, data=self.nacos_login_data, verify=False)
        if response.status_code == 200:
            token = response.json()["accessToken"]
            return token
        else:
            print("登陆失败")
            return None
    
    def get_all_namespace_list(self):
        """获取nacos命名空间列表"""
        query_url = 'http://' + self.clientUrl + ':8848/nacos/v1/console/namespaces'
        headers = {
            "Accept": "application/json"
        }
        response = requests.get(url=query_url, headers=headers, params={"accessToken": self.token}, verify=False)
        if response.status_code == 200:
            namespace_list = response.json()["data"]
            return namespace_list
        else:
            print("命名空间列表获取失败")
            print(response.content)
            return None
    
    def get_all_config(self):
        """获取的所有的配置名称"""
        namespace = self.get_all_namespace_list() #命名空间列表
        config_list = []
        for np in namespace:
            npname = np['namespace'] #命名空间
            npNum = np['configCount'] #命名数量
            offsets = npNum/10
            coffset = npNum % 10
            if coffset != 0:
                offsets += 1
            for npn in range(1,int(offsets)+1):
                query_url = 'http://' + self.clientUrl + ':8848/nacos/v1/cs/configs?dataId=&group=&appName=&config_tags=&pageNo={page}&pageSize=10&tenant={namespace}&search=accurate'.format(namespace=npname,page=npn)
                headers = {
                    "Accept": "application/json"
                }
                response = requests.get(url=query_url, headers=headers, params={"accessToken": self.token}, verify=False)
                if response.status_code == 200:
                    configData = response.json()
                    for pit in configData['pageItems']:
                        config_list.append(pit)
        return config_list
        


    def get_all_configInfo(self):
        '''获取所有的配置内信息'''
        cfgDetail = self.get_all_config()
        cfgDetailList = list()
        for cfg in cfgDetail:
            dataId = cfg['dataId']
            group = cfg['group']
            tenant = cfg['tenant']
            dic = dict()

            query_url = 'http://' + self.clientUrl + ':8848/nacos/v1/cs/configs?show=all&dataId={dataId}&group={group}&tenant={tenant}'.format(dataId=dataId,group=group,tenant=tenant)
            headers = {
                "Accept": "application/json"
            }
            response = requests.get(url=query_url, headers=headers, params={"accessToken": self.token}, verify=False)
            if response.status_code == 200:
                cfgDetaildict = response.json()
                dic['dataId'] = cfgDetaildict['dataId']
                dic['group'] = cfgDetaildict['group']
                dic['content'] = cfgDetaildict['content']
                dic['md_five'] = cfgDetaildict['md5']
                dic['tenant'] = cfgDetaildict['tenant']
                dic['type'] = cfgDetaildict['type']
                dic['valueMethod'] = 'auto'
                dic['dataStatus'] = 'effective'
                dic['valueMethodAdd'] = 'http://'+self.clientUrl
                cfgDetailList.append(dic)
        endic  = dict()
        endic['CIT_Nacos'] = cfgDetailList
        print(json.dumps(endic))

if __name__ == '__main__':
    # #设置传入参数
    parser = OptionParser()
    parser.add_option('--clientUrl', type=str, dest='clientUrl',default='')
    parser.add_option('--nacosUsername', type=str, dest='nacosUsername',default='')
    parser.add_option('--nacosPasswrod', type=str,dest='nacosPasswrod', default='')

    #获取传入参数
    (options, args) = parser.parse_args()
    clientUrl = options.clientUrl
    nacosUsername = options.nacosUsername
    #nacosPasswrod = options.nacosPasswrod
    nacosPasswrod=des_decrypt(options.nacosPasswrod)

    nacos = getNacosInfo(clientUrl,nacosUsername,nacosPasswrod)
    nacos.get_all_configInfo()
