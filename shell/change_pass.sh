#!/bin/bash


IPLIST="
10.0.0.100
10.0.0.7
"
PASS=centos1
. /etc/os-release

pre_os () {
if [[ $ID =~ ubuntu ]];then
   dpkg -l  sshpass &> /dev/null || { apt update; apt -y install sshpass; }
elif [[ $ID =~ rocky|centos|rhel ]];then
    rpm -q sshpass &>/dev/null || yum -y install sshpass
else
    echo "不支持当前操作系统"
    exit
fi

}

change_root_pass () {

[ -f ip_pass.txt ] && mv ip_pass.txt ip_pass.txt.bak

for ip in $IPLIST;do
    pass=`openssl rand -base64 9` 
    sshpass -p $PASS  ssh -o StrictHostKeyChecking=no  $ip "echo root:$pass | chpasswd" 
    if [ $? -eq 0 ];then
        echo  "$ip:root:$pass" >> ip_pass.txt
        echo "change root password is successfull on $ip"
    else
        echo "change root password is failed on $ip"
    fi
done

}

pre_os

change_root_pass

