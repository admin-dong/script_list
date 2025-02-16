#!/bin/bash
# 安装Docker的自动化脚本

# 检查是否以root用户运行脚本，如果不是则退出
if [ "$(id -u)" -ne 0 ]; then
  echo "请以root用户或使用sudo运行此脚本。"
  exit 1
fi

# Step 1: 安装必要的一些系统工具
echo "安装必要的系统工具..."
yum install -y yum-utils

# Step 2: 添加软件源信息
echo "添加Docker软件源信息..."
yum-config-manager --add-repo https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo

# Step 3: 安装Docker及其相关组件
echo "安装Docker及其相关组件..."
yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Step 4: 开启Docker服务并设置开机自启
echo "开启Docker服务并设置开机自启..."
systemctl start docker
systemctl enable docker

# 检查Docker服务状态
echo "检查Docker服务状态..."
systemctl status docker

echo "Docker安装完成！"
