##title 适用于为webhook
# Update :
import json
import requests
import datetime
import logging
from flask import Flask, request
from dateutil import parser
from jinja2 import Template



# qywechat
wx_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=e5106337-5f7a-4cd5-b932-d98a2532f441"
#wx_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/
#send?key=8b1203bf-f0c4-4996-805c-e13dbb48ac27"
#定义日志模块
logfile = "push.log"
logger = logging.getLogger(__name__) 
logger.setLevel(level=logging.INFO)
handler = logging.FileHandler(logfile)
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
'%(asctime)s - %(name)s - %(levelname)s - %(message)s') 
handler.setFormatter(formatter)
logger.addHandler(handler)


#定义模板
alert_template = """
告警名称:{{alert_name }}
告警实例:{{ alert_item }}
告警job:{{ alert_severity }}
告警级别:{{ alert_level?}}
告警状态:{{ alert_state }}
告警概述:{{alert_summary }}
告警详情:{{ alert_description}}
告警时间:{{alert_activetime
"""
resolve_template = """
告警名称:{{alert_name
告警实例:{{alert_item}}
告警job:{{alert_severity}}
告警级别:{{alert_level}}
告警状态:{{alert_state}}
告警概述:{{alert_summary}}
告警详情:{{alert_description}}
告警时间:{{alert_activetime}}
恢复时间:{{alert_resovetime}}
"""

##时区转换
def time_zone_conversion(utctime):  
    format_time = parser.parse(utctime).strftime('%Y-%m-%dT%H:%M:%SZ')  
    time_format = datetime.datetime.strptime(format_time, "%Y-%m-%dT%H:%M:%SZ")  
    return str(time_format + datetime.timedelta(hours=8)) 




def jinjia2_write(**kwargs):  
    print("kwargs:", json.dumps(kwargs))  
    alert_jinjia2 = {}  
    print("---", alert_jinjia2)  
    alert_jinjia2['alert_state'] = '告警发生' if kwargs['status'] == 'firing' else '告警恢复'  
    alert_jinjia2['alert_item'] = kwargs['labels']['instance']  
    alert_jinjia2['alert_name'] = kwargs['labels']['alertname']  
    alert_jinjia2['alert_level'] = kwargs['labels']['severity']  
    alert_jinjia2['alert_serverity'] = kwargs['labels']['job']  
    alert_jinjia2['alert_description'] = kwargs['annotations']['description']  
    alert_jinjia2['alert_activetime'] = time_zone_conversion(kwargs['startsAt'])  
      
    if alert_jinjia2['alert_state'] == '告警发生':  
        template = Template(alert_template)  
    else:  
        alert_jinjia2['alert_resovetime'] = time_zone_conversion(kwargs['endsAt'])  
        template = Template(resolve_template)  
      
    message = template.render(alert_jinjia2)  
    return message  # 返回渲染后的消息字符串



def wx_robot(message):  
    headers = {"Content-Type": "application/json"}  
    data = {  
        "msgtype": "markdown",  
        "markdown": {"content": message}  
    }  
    wx_url = '你的微信机器人URL'  # 需要你提供实际的URL  
    r = requests.post(wx_url, headers=headers, data=json.dumps(data))  
    logger.info("发送告警信息\n{message}".format(message=message))  
    return r  

app = Flask(__name__)  
  
@app.route('/alertinfo', methods=['POST'])  
def alertinfo():  
    if request.method == 'POST':  
        try:  
            data = json.loads(request.data)  
            logger.info("接收到alertmanager的推送post请求，开始解析告警信息")  
            alert_list = []  
            for totalMsg in data.get('alerts', []):  # 使用.get()以处理'alerts'键不存在的情况  
                alert_list.append(parse_alert(**totalMsg))  # 假设parse_alert能处理**kwargs  
  
            msg = "======异常告警=======\n{}\n=========END=========".format("\n".join(alert_list))  
            wx_robot(msg)  # 发送消息到微信机器人  
            return "ok"  
        except Exception as e:  
            logger.error(f"处理告警信息时发生错误: {e}")  # 使用f-string格式化错误信息  
            return "error", 500  # 返回HTTP 500错误码 


if  __name__=='_main_':
    app.run(debug=False,host='0.0.0.0',port=5001,)
    
# #
# 这个脚本是一个使用Flask框架编写的Web服务，旨在接收来自Alertmanager（或其他监控系统）的Webhook通知，并将这些通知转换为格式化的消息，然后发送给微信企业号的机器人（Webhook）。这个过程涉及到告警信息的解析、模板渲染和消息发送。下面是对脚本主要部分的详细解释：

# 1. 导入必要的库
# json：用于处理JSON数据。
# requests：用于发送HTTP请求。
# datetime 和 dateutil.parser：用于处理日期和时间。
# logging：用于记录日志。
# Flask 和 request：Flask是一个轻量级的Web应用框架，request用于接收客户端发送的请求。
# jinja2.Template：用于模板渲染，将告警信息填充到预定义的模板中。
# 2. 定义常量和配置
# wx_url：微信企业号机器人的Webhook URL（但请注意，示例中的URL是无效的，你需要替换为实际的URL）。
# 日志配置：设置日志级别、格式和文件处理器。
# 3. 定义模板
# alert_template 和 resolve_template：定义了两个Jinja2模板，分别用于渲染告警发生和告警恢复的消息。
# 4. 时区转换函数
# time_zone_conversion：将UTC时间转换为指定时区（这里是东八区）的时间。
# 5. 消息渲染函数
# jinjia2_write：根据传入的告警信息（通过**kwargs接收），渲染相应的模板并返回消息字符串。
# 6. 发送消息到微信的函数
# wx_robot：将渲染后的消息作为Markdown类型的内容，通过POST请求发送到微信企业号机器人的Webhook URL。
# 7. Flask应用
# 定义了一个Flask应用，并定义了一个路由/alertinfo来处理POST请求。
# 当接收到POST请求时，解析请求体中的JSON数据，对每个告警信息进行解析和渲染，然后将所有告警信息组合成一条消息发送给微信机器人。
# 如果处理过程中发生异常，则记录错误日志并返回HTTP 500错误码。
# 8. 错误和需要注意的地方
# 脚本中的parse_alert函数没有在代码中定义，但在alertinfo路由的处理函数中被调用。这意味着你需要自己实现这个函数，或者如果你只是想简单测试，可以直接在循环中调用jinjia2_write函数。
# 脚本中的if __name__=='_main_':行有一个拼写错误，应该是if __name__ == '__main__':。
# wx_url在wx_robot函数内被重新赋值，但这实际上是多余的，因为你已经在脚本开头定义了它。
# 请确保替换wx_url为你实际的微信企业号机器人Webhook URL。
# 日志文件中的信息对调试和监控服务非常有用，确保你有权访问该日志文件。
# 这个脚本是一个很好的示例，展示了如何使用Flask和微信企业号机器人来处理和发送告警通知。