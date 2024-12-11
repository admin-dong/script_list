-*- coding: utf-8 -*-
from time import sleep
from selenium.common.exceptions import ElementClickinterceptedE:xception
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from PIL import Image
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.header import Header
import time
from WorkWeixinRobot.work_weixin_robot import WWXRobot
import os
chrome_options=Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920,4050") :#thekey解决grafana页面无法最大化问题
chrome_options.add_argument('--no-sandbox')#设置
driver=webdriver.Chrome(executable_path=
(r'/root/selenium/chromedriver94'),chrome_options=chrome_coptions
driver.implicitly_wait(1)
feed_地址='https://grafana.painet.work/d/KFURQFdnz/bai-du-feedri-bao-shu-ju-mian-ban-shu-ban?
orgId=1&from=now-1d%2Fd&to=now-1d%2Fd
xcdn_地址='https://grafana.painet.work/d/MGFREBFnk/bai-du-xcdnri-bao-mian-xiang-ke-hu?orgId=1&from=now
1d%2Fd&to=now-1d%2Fd"
#ks_地址='https://grafana.painet.work/d/qM_75Qvnk/9-kuai-shnou-zi-yuan-pao-liang-ri-bao?orgid=1&from=now
1d%2Fd&to=now-1d%2Fd
bdwphj_地址='https://grafana.painet.work/d/Tjpe38S7z/bai-du-wang-pan-hui-ju-ri-bao-shu-ju-mian-ban?
orgId=1&from=now-1d%2Fd&to=now-1d%2Fd
dcache_地址='https://grafana.painet.work/d/olAd1_Dnz/7-ai-qi-yi-ri-bao-shu-ju-mian-ban?orgId=1&refresh=1d'
bdr_地址='https://grafana.painet.work/d/rHyYIsI7z/bai-du-rong-qi-bdrri--bao-shu-ju-mian-ban-mian-xiang-ke-hu?
orgId=1&from=now-1d%2Fd&to=now-1d%2Fd
def shootscreen(fun_driver,地址,sleep_time,box_size,wx_key):
fun_driver.get(地址)
width = driver.execute_script("return document.documentElerment.scroll Width")
fun_driver.set_window_size(width, 4050)
sleep(sleep_time)
fun_driver.save_screenshot('/root/selenium/web.png')
box = (70,65,1920,box_size)#for lupaus philips row in #上距,右宽,下宽
im=Image.open('/root/selenium/web.png')
img=im.crop(box)
img.save('/root/selenium/screen_web.png')
wwx=WWXRobot(key=wx_key)#测试
wwx.send_image(local_file='/root/selenium/screen_vveb.png'
def send_mail(mail_cc,mail_to,mail_subject,fun_mail_msg):
endDate=time.strftime('%Y-%m-%d',time.localtime(time.time())())
smtp_server = 'smtp.partner.outlook.cn'
from_addr ='xiaoxin@pplabs.org'
passwd = 'PPIO.12345'
fp = open('/root/selenium/screen_web.png', 'rb')
msgImage = MIMEImage(fp.read())
fp.close()
msgRoot = MIMEMultipart('related')
msgRoot['From'] = Header(" PPIO", 'utf-8')
#msgRoot['To'] = Header("", 'utf-8')
msgRoot['Cc']=mail_cc
msgRoot['To']=mail_to
#msgRoot['To']='xiaoxin@pplabs.org'
subject = str(endDate)+mail_subject
#testing option
msgRoot['Subject'] = Header(subject, 'utf-8')
msgAlternative = MIMEMultipart('alternative')
msgRoot.attach(msgAlternative)
mail_msg =fun_mail_msg
msgAlternative.attach(MIMEText(mail_msg, 'html', 'utf-8'))
msgImage.add_header('Content-ID', '<image1>')
msg Root.attach(msgImage)
try:
#smtpObj = smtplib.SMTP_SSL(smtp_server)
smtpObj = smtplib.SMTP(smtp_server,587)
#smtpObj.connect(smtp_server, 465) # 465为SL端口号
smtpObj.connect(smtp_server, 587) # 587为SSL端口号
smtpObj.starttls() #打开TLS
smtp Obj.login(from_addr,passwd)
#smtpObj.sendmail(data, msgRoot.as_string())
smtpObj.sendmail(from_addr,msgRoot['To'].split(","),msgRoot.as__string())
print("邮件发送成功")
except smtplib.SMTPException as e:
print("Error:无法发送邮件")
print(e)
smtpObj.close()
if name == "__main__":
driver.get(feed_地址)
driver.find_element_by_xpath('/html/body/grafana-app/div/div/react
container/div/div/div[2]/div/div/form/div[1]/div[2]/div/div/input').send_keys("xiaoxin@pplabs.org")
driver.find_element_by_xpath('/html/body/grafana-app/div/div/div/reaact-
container/div/div/div[2]/div/div/form/div[2]/div[2]/div/div/input').sendkeys("********)
driver.find_element_by_xpath('/html/body/grafana-app/div/div/react
container/div/div/div[2]/div/div/form/button').click()
sleep(1)
#next,xcdn
shootscreen(driver,xcdn_地址,100,3400, 08b47741-6bb6-47bf-b2d4-4f8f7cf705ec')#XCDN日报
bdx_mail_to='xcdner@.com,xiaoxin@pplabs.org'
bdx_mail_cc='oubu@pplabs.org,pengpeng@pplabs.org'
bdx_mail_subject='XCDN业务日报'
bdx_mail_msg = """"
<p>XCDN业务昨日日报</p>
<p></p>
<p><img src="cid:image1"></p>
send_mail(bdx_mail_cc,bdx_mail_to,bdx_mail_subject,bdx_maail_msg
#next,bdr
shootscreen(driver,bdr_地址,60,1490,'08b47741-6bb6-47bf-b2d44-4f8f7cf705ec') #bdr日报
bdr_mail_to='wuyongqiang@.com,zhangfushan@.ccom,chemiao@.com, wangyuxiang03@
com,xiaoxin@pplabs.org,wuliuqi@pplabs.org"
bdr_mail_cc='oubu@pplabs.org,pengpeng@pplabs.org"
bdr_mail_subject='容器业务日报'
bdr_mail_msg = """"
<p>容器业务昨日日报</p>
<p></p>
<p><img src="cid:image1"></p>
send_mail(bdr_mail_cc,bdr_mail_to,bdr_mail_subject,bdr_mai_msg)
driver.close()