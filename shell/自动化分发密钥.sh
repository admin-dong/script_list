# 创建密钥对
# ssh-keygen -t rsa 
# #注意创建的啥时候也可以不加-t 
# 通过rsa方法对数据进行加密.
# 分发公钥
# ssh-copy-id -i /root/.ssh/id_rsa.pub     
# root@10.0.0.41
# 连接测试
# ssh root@10.0.0.41 hostname -I
# 温馨提示: 
# ssh-copy-id后公钥被存放在对方服务器的用户家目录下面的.ssh下面. 
# 名字叫:authorized_keys

#
#自动化创建密钥

# ssh-keygen -t rsa -f ~/.ssh/id_rsa -P ''
# 要下载一下sshpass
# yum install sshpass


#分发
#!/bin/bash

#
pass=123456
ips="10.0.0.61 10.0.0.41 10.0.0.31 10.0.0.7 10.0.0.100 10.0.0.101"
. /etc/init.d/functions

#1.1 检查是否联网
  if ping -c 1 8.8.8.8 &>/dev/null;then
     if [ $? -eq 0 ];then
     echo "网络正常"
     else 
     echo "网络连接不可用"
     fi
fi

# 1.2 检查yum是否可以使用
  if  command -v yum &>/dev/null;then
     if [ $? -eq 0 ];then
     echo "yum 正常"
     else
     echo "yum 异常"
     fi
fi
#1.3 判断 sshpass 是否存在
if ! command -v sshpass &>/dev/null;then
    echo " $ip sshpass 未安装,在尝试用yum安装"
    sudo yum -y install sshpass &/dev/null
    if [ $? -eq 0];then 
    echo " $ip yum 安装sshpass成功"
    else 
    echo "$ip  yum 安装失败"
    exit 1
    fi
fi
# 2.创建密钥对
if [ -f ~/.ssh/id_rsa ] ; then
   echo "已经创建过密钥了"
else
  echo "正在创建密钥对"
  ssh-keygen -t rsa -f ~/.ssh/id_rsa -P '' &>/dev/null
  if [ $? -eq 0 ]; then
	action "密钥对创建成功" /bin/true
  else 
    	action "密钥对创建失败" /bin/false
  fi
fi

#3.通过循环发送
for ip in $ips
do
 echo "正在向$ip 发送公钥"
 sshpass -p${pass} ssh-copy-id -i ~/.ssh/id_rsa.pub  -oStrictHostKeyChecking=no $ip &>/dev/null 
 if [ $? -eq 0 ];then
  	action "$ip 公钥分发成功" /bin/true
 else 
	action "$ip 公钥分发失败" /bin/false
 fi 
done


#判断

for   ip  in  10.0.0.7  10.0.0.31   
do
    ssh  $ip   hostname 
done