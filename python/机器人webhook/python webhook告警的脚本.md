python webhook告警的脚本

zabbix 配置告警用的

```
#1.企业微信 id号
企业ID
ww6ac68d5d41044330
#2.创建1个报警机器人(应用)
Վˁ
机器人的id(应用id)  
AgentId
1000005
Վˁ
应用密码  
Ss7VFx8Mkzm8XABMNqVRp31zxNnxhbJ_rJzz8sPDgk4
#修改微信报警的脚本
vim /usr/local/share/zabbix/alertscripts/wechat.py
```

python

```
import requests
import sys
import os
import json
import logging
logging.basicConfig(level = logging.DEBUG, format = 
'%(asctime)s, %(filename)s, %(levelname)s, %
(message)s',
               datefmt = '%a, %d %b %Y %H:%M:%S',
               filename = 
os.path.join('/tmp','wechat.log'),
               filemode = 'a')
#id和secret需要修改
corpid='wxd074861951c67ba6'
appsecret='QtraZrI936DZ0jZ3aSWTZlFVheAMgLmq3toM4B9U1A'
agentid=1
#获取accesstoken
token_url='https:Վˌqyapi.weixin.qq.com/cgibin/gettoken?corpid=' + corpid + '&corpsecret=' + 
appsecret
req=requests.get(token_url)
accesstoken=req.json()['access_token']
#发送消息
msgsend_url='https:Վˌqyapi.weixin.qq.com/cgibin/message/send?access_token=' + accesstoken
#脚本参数
#touser=sys.argv[1]
toparty=sys.argv[1]
subject=sys.argv[2]
#toparty='3|4|5|6'
message=sys.argv[2] + "\n\n" +sys.argv[3]
params={
#       "touser": touser,
       "toparty": toparty,
        "msgtype": "text",
        "agentid": agentid,
        "text": {
                "content": message
       },
        "safe":0
}
req=requests.post(msgsend_url, 
data=json.dumps(params))
logging.info('sendto:' + touser + 'Վʮsubject:' + 
subject + 'Վʮmessage:' + message)        
```

环境依赖

```
#安装python环境
yum install -y python3 python3-pip
通过pip3 命令安装requests依赖.
pip3 install -i 
https:Վˌpypi.tuna.tsinghua.edu.cn/simple requests
```

测试

```
#测试
python3 wechat.py 用户的id或组id 标题   内容
'下雨了'  '打雷下雨收衣服'
```

\#web页面 发件人:报警媒介类型 

{ALERT.SENDTO}  #发给谁 

{ALERT.SUBJECT} #报警标题 

{ALERT.MESSAGE} #报警内容

故障目前已经解决时间: {EVENT.RECOVERY.TIME} 日期 

{EVENT.RECOVERY.DATE} 

故障名称: {EVENT.NAME} 

故障经历多久: {EVENT.DURATION} 

故障主机: {HOST.NAME} 

故障级别: {EVENT.SEVERITY} 

故障ID: {EVENT.ID} 

{TRIGGER.URL}

需要去企业微信后台,开通白名单

![img](https://cdn.nlark.com/yuque/0/2024/png/35538885/1721615400645-e155a284-2a84-4c1e-997a-9161fdf228ce.png)

另外一个版本

```
#!/usr/bin/env python
#-*- coding: utf-8 -*-
#author: oldboy-linux
#date: 2021
#description: Zabbix Wechat Alerts Scripts

import requests
import sys
import os
import json
import logging

logging.basicConfig(level = logging.DEBUG, format = '%(asctime)s, %(filename)s, %(levelname)s, %(message)s',
                datefmt = '%a, %d %b %Y %H:%M:%S',
                filename = os.path.join('/tmp','wechat.log'),
                filemode = 'a')

#id和secret需要修改
corpid='ww6ac68d5d41044330'
appsecret='3Fa1aSoYg5O0BsHrpOrQ6Qc7EzqcFHlWlZ2U4o3Qtls'
agentid=1000003
#获取accesstoken
token_url='https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=' + corpid + '&corpsecret=' + appsecret
req=requests.get(token_url)
accesstoken=req.json()['access_token']

#发送消息
msgsend_url='https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + accesstoken

#脚本参数
touser=sys.argv[1]
subject=sys.argv[2]
#toparty='3|4|5|6'
message=sys.argv[2] + "\n\n" +sys.argv[3]

params={
        "touser": touser,
#       "toparty": toparty,
        "msgtype": "text",
        "agentid": agentid,
        "text": {
                "content": message
        },
        "safe":0
}

req=requests.post(msgsend_url, data=json.dumps(params))

logging.info('sendto:' + touser + ';;subject:' + subject + ';;message:' + message) 

```