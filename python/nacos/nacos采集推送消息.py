#!/usr/bin/python
# -*- coding: utf-8-*-
# import schedule
import json
import requests
import time
from pyDes import *
from optparse import OptionParser
from binascii import a2b_hex
import ctypes,sys
# import io
from operator import itemgetter
from itertools import groupby
defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)

def des_decrypt(message):
    k = des('dsasdadaj', ECB, padmode=PAD_PKCS5)
    return k.decrypt(a2b_hex(message)).decode('utf8')
def data(viewid,env):
    auth_url = 'http://10.1.2.14:9069/login/direct'
    response = requests.post(
        url=auth_url,
        headers={
            'content-type': 'application/json',
            'accept': 'text/html,application/json',
        },
        data=json.dumps({
            'username': ljqusername,
            'password': ljqpassword
        })

    )
    token = json.loads(response.text).get('param')
    net_list = []
    url = 'http://10.1.2.14:9069/view/direct'
    headersa = {
        'content-type': 'application/json',
        'accept': 'text/html,application/json',
        'Authorization': token
    }
    aaa = {
    "queryCondition": [],
    "viewid": viewid,
    "startPage": 1,
    "pageSize": 1000,
    "moduleName": "查看",
    "name": "查看"
    }
    resp = requests.post(url=url, headers=headersa, data=json.dumps(aaa))
    eamm = resp.text.replace("\"success\":true,", "")
    ep = json.loads(eamm)
    total = ep.get('param').get('total')
    offsets = total/1000
    offset = total % 1000
    if offset != 0:
        offsets += 1
    for i in range(1, offsets+1):
        ccc = {
            "queryCondition": [
                    {
                        'key': "env",
                        'operation': 'eq',
                        'value': env
                    },
                    {
                        'key': "nameSpace",
                        'operation': 'eq',
                        'value': namespace
                    }
                ],
            "viewid": viewid,
            "startPage": i,
            "pageSize": 1000,
            "moduleName": "nacos服务信息数据获取",
            "name": "nacos服务信息数据获取"
        }

        respa = requests.post(url=url, headers=headersa, data=json.dumps(ccc))
        pullData = json.loads(respa.text.replace("\"success\":true,", ""))['param']['content']
    #     # localtime = int(time.mktime(time.strptime((datetime.datetime.now()+datetime.timedelta(days=-3)).strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")))
        # pullData.sort(key=itemgetter('nameSpace'))
        # for date, items in groupby(pullData, key=itemgetter('nameSpace')):
        #    print(list(items))
            # print(json.dumps(list(items),ensure_ascii=False,indent=2))
            # net_list.append(list(items))

        for n in pullData:
            net_list.append(n)
    
    return net_list

def feishu_webhook(sendto,message):
    url = sendto
    payload_message = {
    "msg_type": "interactive",
    "card": {
        "elements": [{
                "tag": "div",
                "text": {
                        "content": message,
                        "tag": "lark_md"
                }
        }],
        "header": {
                "title": {
                        "content": "nacos服务状态告警",
                        "tag": "plain_text"
                },
                "template":"red" # 卡片标题颜色
        }
    }
    }
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=json.dumps(payload_message))
    return response

class getNacosInfo():
    def __init__(self,clientUrl,nacosUsername,nacosPasswrod,namespace,env):
        self.clientUrl = clientUrl
        self.nacosUsername = nacosUsername
        self.nacosPasswrod = nacosPasswrod
        self.namespace = namespace
        self.env = env
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
        try:
            response = requests.post(url=loginUrl, headers=headers, data=self.nacos_login_data, verify=False)
            if response.status_code == 200:
                token = response.json()["accessToken"]
                return token
        except:
            print("登陆失败")
            # return None
    
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
            # printRedgreen("命名空间列表获取失败")
            # print(response.content)
            return None
    
    def get_all_config(self):
        """获取的所有的配置名称"""
        namespaces = self.get_all_namespace_list() #命名空间列表
        config_list = []
        nacosinfo = data(viewid,env)
        for np in namespaces:
            if np['namespace'] == self.namespace: #"middle-platform":
                npname = np['namespace'] #命名空间
                npNum = np['configCount'] #命名数量
                # offsets = npNum/100
                # coffset = npNum % 100
                # if coffset != 0:
                #     offsets += 1
                # for npn in range(1,int(offsets)+1):
                    # query_url = 'http://' + self.clientUrl + ':8848/nacos/v1/ns/catalog/services?dataId=&group=&appName=&config_tags=&pageNo={page}&pageSize=10&tenant={namespace}&search=accurate'.format(namespace=npname,page=npn)
                query_url = 'http://' + self.clientUrl + ':8848/nacos/v1/ns/catalog/services?hasIpCount=true&withInstances=false&pageNo=1&pageSize=100&namespaceId={namespace}'.format(namespace=npname)
                headers = {
                    "Accept": "application/json"
                }
                response = requests.get(url=query_url, headers=headers, params={"accessToken": self.token}, verify=False)
                if response.status_code == 200:
                    configData = response.json()
                    service_list = []
                    service_err_list = []
                    for service in nacosinfo:#[j.get('name') for j in configData.get('serviceList')]:
                        item = dict()
                        if service.get('serviceName') in [i['name'] for i in configData.get('serviceList')]:
                            item['servicename'] = service.get('serviceName')
                            item['status'] = "True"
                            item['datastatus'] = "effective"
                            item['nameSpace'] = service.get('nameSpace')
                            item['nacosIP'] = service.get('nacosIP')
                            service_list.append(item)
                        else:
                            service_err_list.append(service.get('serviceName'))
                            item['servicename'] = service.get('serviceName')
                            item['status'] = "False"
                            item['nameSpace'] = service.get('nameSpace')
                            item['nacosIP'] = service.get('nacosIP')
                            service_list.append(item)
                    if service_err_list != []:
                        message = '【{}】 {} nacos【{}】namespace的【{}】服务掉了'.format(self.env,clientUrl,self.namespace,','.join(service_err_list))
                        feishu_webhook(webhook,message)
                    print(json.dumps({'CIT_NacosServiceInfo':service_list},ensure_ascii=False,indent=2))
                else:
                    print("连接失败")

if __name__ == '__main__':
    # #设置传入参数
    parser = OptionParser()
    parser.add_option('--viewid', type=str, dest='viewid',default='')
    parser.add_option('--ljqusername', type=str, dest='ljqusername',default='')
    parser.add_option('--ljqpassword', type=str, dest='ljqpassword',default='a')
    parser.add_option('--webhook', type=str, dest='webhook',default='')
    parser.add_option('--clientUrl', type=str, dest='clientUrl',default='')
    parser.add_option('--nacosUsername', type=str, dest='nacosUsername',default='')
    parser.add_option('--nacosPasswrod', type=str,dest='nacosPasswrod', default='')
    parser.add_option('--namespace', type=str,dest='namespace', default='')
    parser.add_option('--env', type=str,dest='env', default='')

    #获取传入参数
    (options, args) = parser.parse_args()
    clientUrl = options.clientUrl
    nacosUsername = options.nacosUsername
    viewid = options.viewid
    ljqusername = options.ljqusername
    # nacosPasswrod = options.nacosPasswrod
    #ljqpassword = options.ljqpassword
    webhook = options.webhook
    nacosPasswrod=des_decrypt(options.nacosPasswrod)
    ljqpassword=des_decrypt(options.ljqpassword)
    namespace = options.namespace
    env = options.env
    # nacosinfo = data(viewid,env)
    # print(json.dumps(nacosinfo,ensure_ascii=False,indent=2))
    nacos = getNacosInfo(clientUrl,nacosUsername,nacosPasswrod,namespace,env)
    nacos.get_all_config()
