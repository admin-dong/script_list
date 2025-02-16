#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
DOWNLOAD_URL=https://dl.google.com/go/go1.23.5.linux-amd64.tar.gz

# 检查是否具有 sudo 权限
if [ "$(id -u)" != "0" ]; then
   echo -e "${RED}This script must be run as root or with sudo.${NC}"
   exit 1
fi

echo -e "${GREEN}Starting Go installation...${NC}"

# 下载并解压Go安装包


curl -O $DOWNLOAD_URL
tar -zxvf go1.23.5.linux-amd64.tar.gz -C /usr/local

# 配置环境变量
echo 'export PATH=$PATH:/usr/local/go/bin' >> /etc/profile
source /etc/profile

# 测试安装是否成功
echo -e "${GREEN}Testing Go installation...${NC}"
go version
if ! command -v go &> /dev/null; then
    echo -e "${RED}Go installation failed.${NC}"
    exit 1
else
    echo -e "${GREEN}Go installed successfully!${NC}"

    # 设置 GOPROXY
    echo -e "${GREEN}Setting GOPROXY to https://goproxy.cn,direct...${NC}"
    go env -w GOPROXY=https://goproxy.cn,direct

    # 验证 GOPROXY 设置是否成功
    CURRENT_GOPROXY=$(go env GOPROXY)
    if [[ "$CURRENT_GOPROXY" == "https://goproxy.cn,direct" ]]; then
        echo -e "${GREEN}GOPROXY set successfully to https://goproxy.cn,direct.${NC}"
    else
        echo -e "${RED}Failed to set GOPROXY. Current value: ${CURRENT_GOPROXY}${NC}"
    fi
fi