
#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@LastDebugTime :2023/12/26 15:25:10,
@Env           :python2
"""
import requests
import json
import ssl
import sys
try:
    from TypeConversion import res  # 调用公共类，输入模块
    from TypeConversion import outPutTable  # 调用公共类，表格输出模块
except Exception as error:
    print(error)
    exit(1)
defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)

class dataQuery(object):
    def __init__(self):
        #not in
        self.Not_list = [[],'',None]
        #流程传入组件
        self.behavior=res.get('behavior')
        self.jar_info=res.get('jar_info')
        self.zabbix_dict=res.get('zabbix_dict')
        #飞书地址
       
    def send_message(self,message,theme):
        urls = self.zabbix_dict['notification']
        #判断告警等级
        level=self.zabbix_dict['TRIGGER.SEVERITY']
        if "Information" == level:
            colour = "blue"
        if "Warning(警告)" == level:
            colour = "yellow"
        if "Average(一般严重)" == level:
            colour = "orange"
        if "High(严重)" == level:
            colour = "red"
        if "Disaster(灾难)" == level:
            colour = "red"
        if "Not classified" == level:
            colour = "grey"
        if self.behavior == "重启成功":
            colour="green"
        #判断标题
        # if  "服务重启" 
        payload_message = {
            "msg_type": "interactive",
            "card": {
                "elements":[
                 {
                    "tag": "div",
                    "text": {
                        "content": message,
                        "tag": "lark_md"
                    }
                }
                ],
                "header": {
                    "title": {
                        "content": theme,
                        "tag": "plain_text"
                    },
                    "template": colour # 卡片标题颜色
                }
        }
        }
    
        headers = {
            'Content-Type': 'application/json'
        }
        for url in urls:
            response = requests.request("POST", url, headers=headers, data=json.dumps(payload_message))
            print(response.text)
    def send_feishu(self):
        message=self.zabbix_dict['TITLE']
        if self.behavior == "重启服务":
            theme= '对虚机: {} 执行重启 {} 服务操作'.format(self.zabbix_dict['HOST.IP'],self.jar_info['jar_name'])
        if self.behavior == "重启服务失败":
            theme= '因虚机: {} 重启 {} 服务失败,将执行重启虚拟机操作'.format(self.zabbix_dict['HOST.IP'],self.jar_info['jar_name'])
        if self.behavior == "重启机器":
            theme= '因服务重启失败，对虚机: {} 进行重启操作'.format(self.zabbix_dict['HOST.IP'])
        if self.behavior == "重启成功":
            theme= '重启 {} 虚机 {} 服务成功'.format(self.zabbix_dict['HOST.IP'],self.jar_info['jar_name'])
        if self.behavior == "人工":
            theme= '虚拟机 {} 重启 {} 服务流程失败,建议人工检查'.format(self.zabbix_dict['HOST.IP'],self.jar_info['jar_name'])
        self.send_message(message,theme)
if __name__ == '__main__':
    instance = dataQuery()
    instance.send_feishu()