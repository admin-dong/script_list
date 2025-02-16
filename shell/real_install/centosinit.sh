#!/bin/bash

# 更换阿里镜像源
curl -o /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo
if [ $? -eq 0 ]; then
    echo "更换阿里镜像源成功"
else 
    echo "更换阿里镜像源失败"
    exit 1
fi

# 更新阿里云epel源
curl -s -o /etc/yum.repos.d/epel.repo http://mirrors.aliyun.com/repo/epel-7.repo
if [ $? -eq 0 ]; then
    echo "更新阿里云epel成功"
else 
    echo "更新epel失败"
    exit 1
fi

# 关闭firewalld
systemctl disable --now firewalld
if [ $? -eq 0 ]; then
    echo "关闭firewalld成功"
else
    echo "关闭firewalld失败"
    exit 1
fi

# 设置SELinux为disabled（需重启生效）
if grep -q '^SELINUX=enforcing' /etc/selinux/config; then
    sed -i 's/^SELINUX=enforcing$/SELINUX=disabled/' /etc/selinux/config
    setenforce 0  # 立即禁用SELinux而不重启
    if [ $? -eq 0 ]; then
        echo "关闭selinux成功"
    else
        echo "关闭selinux失败"
        exit 1
    fi
else
    echo "SELinux已经是disabled状态，无需再次关闭。"
fi


# 更新所有软件到最新
echo "开始更新所有软件..."
yum update -y
yum makecache

# 安装必要的工具和实用程序（去重后的列表）
echo "开始安装必要的工具和实用程序..."
yum install -y bash-completion curl vim wget httpd-tools tree nmap lrzsz nc lsof tcpdump atop htop iftop nethogs psmisc net-tools stress sysstat vim-enhanced dos2unix yum-utils device-mapper-persistent-data lvm2 bcc-tools libbcc-examples linux-headers-$(uname -r) kernel-devel-$(uname -r) kernel-headers-$(uname -r)
if [ $? -eq 0 ]; then
    echo "yum下载工具成功"
else 
    echo "yum下载工具失败"
    exit 1
fi

echo "所有操作已完成！"