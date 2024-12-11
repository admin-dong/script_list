# -*- coding: utf-8 -*-
from time import sleep
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from PIL import Image
import smtplib
import requests
import json
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.header import Header
import time
from requests_toolbelt import MultipartEncoder
from WorkWeixinRobot.work_weixin_robot import WWXRobot
import os
chrome_options=Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920,3450") #the key 解决grafana页面无法最大化问题
chrome_options.add_argument('--no-sandbox')#设置最大权限
#driver=webdriver.Chrome(executable_path=(r'/root/selenium/chromedriver109'),chrome_options=chrome_options)        #chromedriver路径以及选项设置
driver=webdriver.Chrome(executable_path=(r'/root/selenium/chromedriver109'),chrome_options=chrome_options)        #chromedriver路径以及选项设置
driver.implicitly_wait(1)

url='xxxxxx' ##gr地址
driver.get(url)

driver.find_element_by_xpath('/html/body/div[1]/div/main/div[3]/div/div[2]/div/div[1]/form/div[1]/div[2]/div/div/input').send_keys("business@localhost")
driver.find_element_by_xpath('/html/body/div[1]/div/main/div[3]/div/div[2]/div/div[1]/form/div[2]/div[2]/div/div/input').send_keys("business@123")

js = "window.scrollTo(1000,4000)"
driver.execute_script(js)
#driver.find_element_by_xpath('/html/body/div[1]/div/main/div[3]/div/div[2]/div/div[1]/form/button').click() 

driver.find_element_by_xpath('/html/body/div[1]/div/main/div[3]/div/div[2]/div/div[1]/form/button').click()              #logging
#driver.find_element_by_xpath('/html/body/grafana-app/div/div/react-container/div/div/div[2]/div/div/form/button').click()              #logging
#sleep(10)
width = driver.execute_script("return document.documentElement.scrollWidth")
height = driver.execute_script("return document.documentElement.scrollHeight")
sleep(6)
#input()
#print(width,height)
#input()
driver.set_window_size(width, 3650)
driver.save_screenshot('/root/beijita/tmp/mgtvhj.png')          #截图
driver.close()
#box = (70,60,1650,1140)# for lupaus philips screen;have no row
box = (70,65,1920,1650)# for lupaus philips row in #上距，左距，右宽，下宽
im=Image.open('/root/beijita/tmp/mgtvhj.png')                  #IM读图片
img=im.crop(box)                                                                             #裁剪
img.save('/root/beijita/tmp/mgtvhj.png')
#img.show()
print("截图完毕")
#input()
#######################获取t_token
url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal" ##飞书的回调接口
payload = json.dumps({
    "app_id": "xxxxx",
    "app_secret": "xxxxx"
    # "app_id": "cli_a27284053e",
    # "app_secret": "jdPeEVkwjwjF01vlmKVMgC"
})


headers = {
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)
codejs=response.text
code=json.loads(codejs)
t_token=(code["tenant_access_token"])
print("获取t_token成功")
#######################上传图片
print("图片上传中")
print(t_token)
url = "https://open.feishu.cn/open-apis/im/v1/images" ##回调函数了
form = {'image_type': 'message',
        'image': (open('/root/beijita/tmp/mgtvhj.png', 'rb'))}  # 需要替换具体的path
multi_form = MultipartEncoder(form)
headers = {
    'Authorization': 'Bearer {}'.format(t_token),  ## 获取tenant_access_token, 需要替换为实际的token
}
headers['Content-Type'] = multi_form.content_type
response = requests.request("POST", url, headers=headers, data=multi_form)
print(response.headers['X-Tt-Logid'])  # for debug or oncall
codejs1=(response.content)  # Print Response
code1=json.loads(codejs1)
print("code1 is",code1)

image_key=(code1['data']['image_key'])

#######################发送图片

data = {
        "msg_type": "image",
        "content": {
            "image_key":"{}".format(image_key)

        }
     }
data=json.dumps(data,ensure_ascii=True).encode("utf-8")
#webhook
url = "xxxxx"
header = {
    "Content-type": "application/json",
    "charset":"utf-8"
}
requests.post(url,data=data,headers=header)