#!/usr/bin/python2.7
#_*_coding:utf-8 _*_
 
 
import requests,sys,json
import urllib3
urllib3.disable_warnings()
 
reload(sys)
sys.setdefaultencoding('utf-8')
 
def GetToken(Corpid,Secret):
    Url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    Data = {
        "corpid":Corpid,
        "corpsecret":Secret
    }
    r = requests.get(url=Url,params=Data,verify=False)
    Token = r.json()['access_token']
    return Token
 
def SendMessage(Token,Subject,Content, ProName):
    #Url = "https://qyapi.weixin.qq.com/cgi-bin/appchat/send?access_token=%s" % Token
    Url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s" % Token
    #Data = {
    #    "chatid": "JenkinsAlarm",  # 此处不明白请参考企业微信官网
    #    "msgtype": "text",
    #    "text": {
    #        "content": "[项目名称] : " + ProName + '\n' + "[项目地址] : " + Subject + '\n' + Content + '\n'
    #    },
    #    "safe": "0"
    #}
    data = {
        "touser" : "LiZhenYa",
        "msgtype" : "text",
        "agentid" : 1000002,
        "text" : {
           "content" : "[项目名称] : " + ProName + '\n' + "[项目地址] : " + Subject + '\n' + 
Content + '\n'
        },
        "safe":0
    }
    r = requests.post(url=Url,data=json.dumps(data),verify=False)
    return r.text
 
def action_from_file(filename):
    try:
        str1 = '[变更日志] : '
        with open(filename, 'r') as f:
            for i in f.readlines():
                str1 += i
		            print str1
        if len(str1) == 17:
            str1 += " 无变更"
	# print str1
        return str1
    except Exception as e:
        #print('[ERROR] {0}'.format(e))
	        str1 += str(e)
 
 
if __name__ == '__main__':
    Corpid = "wwa95c9738129a5c8e"
    Secret = "q7Q7IfUOKDWs0WXnN0IF6vESqBpxpV6opVyuSKUxexY"
 
    Subject = sys.argv[1]
    Content = action_from_file(sys.argv[2])
    ProName = sys.argv[3]
 
    Token = GetToken(Corpid, Secret)
    Status = SendMessage(Token,Subject,Content,ProName)
    print Status




# 这个Python脚本的主要作用是通过企业微信API向指定用户（在这个例子中是名为"LiZhenYa"的用户）发送一条包含项目名称、项目地址和变更日志的文本消息。以下是脚本的详细工作流程和各个部分的作用：

# 设置和初始化：
# 导入必要的Python库（requests用于发送HTTP请求，sys用于处理命令行参数，json用于处理JSON数据，urllib3用于禁用SSL警告）。
# 禁用urllib3的SSL警告，并设置Python的默认编码为UTF-8（尽管在Python 3中不再需要这样做，但在Python 2.7中仍然常见）。
# 定义GetToken函数：
# 这个函数负责向企业微信的API发送请求以获取访问令牌（access_token）。
# 它接收企业ID（Corpid）和企业密钥（Secret）作为参数，然后向https://qyapi.weixin.qq.com/cgi-bin/gettoken发送GET请求。
# 请求的响应包含访问令牌，该令牌用于后续请求的身份验证。
# 定义SendMessage函数：
# 这个函数使用之前获取的访问令牌向企业微信API发送文本消息。
# 它构建了一个包含接收者用户ID（touser）、消息类型（msgtype）、应用ID（agentid）、文本内容（text）和安全设置（safe）的JSON数据体。
# 然后，它向https://qyapi.weixin.qq.com/cgi-bin/message/send发送POST请求，请求体是JSON格式的数据。
# 函数返回API响应的文本内容。
# 定义action_from_file函数：
# 这个函数从指定的文件中读取变更日志，并将其作为字符串返回。
# 它首先初始化一个包含"[变更日志] :"的字符串，然后逐行读取文件内容并追加到该字符串中。
# 如果读取的字符串长度恰好为17个字符（这是一个不常见的硬编码检查，可能不是最佳实践），则添加"无变更"的文本。
# 如果读取文件时发生异常，则将异常信息追加到字符串中。
# 主执行逻辑：
# 脚本通过命令行参数接收项目地址（Subject）、变更日志文件路径（用于action_from_file函数）和项目名称（ProName）。
# 使用企业ID和密钥调用GetToken函数获取访问令牌。
# 调用action_from_file函数读取变更日志，并将其作为消息内容的一部分。
# 使用访问令牌、项目地址、变更日志和项目名称调用SendMessage函数发送消息。
# 打印发送消息后返回的API响应文本。
# 注意：脚本中存在一些潜在的问题和改进点，例如硬编码的长度检查、在action_from_file函数中打印日志（这可能不是预期的行为），以及没有检查SendMessage函数返回的响应以确认消息是否成功发送。此外，脚本使用Python 2.7的语法，这可能在未来需要迁移到Python 3。