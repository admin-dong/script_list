#!/bin/bash

NGINX_VERSION=1.20.2
INSTALL_DIR=/apps/nginx

color () {
    RES_COL=60
    MOVE_TO_COL="echo -en \\033[${RES_COL}G"
    SETCOLOR_SUCCESS="echo -en \\033[1;32m"
    SETCOLOR_FAILURE="echo -en \\033[1;31m"
    SETCOLOR_WARNING="echo -en \\033[1;33m"
    SETCOLOR_NORMAL="echo -en \E[0m"
    echo -n "$1" && $MOVE_TO_COL
    echo -n "["
    if [ $2 = "success" -o $2 = "0" ] ;then
        ${SETCOLOR_SUCCESS}
        echo -n $"  OK  "    
    elif [ $2 = "failure" -o $2 = "1"  ] ;then 
        ${SETCOLOR_FAILURE}
        echo -n $"FAILED"
    else
        ${SETCOLOR_WARNING}
        echo -n $"WARNING"
    fi
    ${SETCOLOR_NORMAL}
    echo -n "]"
    echo 
}


install_nginx() {
    wget http://nginx.org/download/nginx-${NGINX_VERSION}.tar.gz || { echo "下载失败!";exit 20;  }
    tar xf nginx-${NGINX_VERSION}.tar.gz -C /usr/local/src
    yum -y install gcc openssl-devel pcre-devel 
    cd /usr/local/src/nginx-${NGINX_VERSION}
    ./configure --prefix=${INSTALL_DIR} --with-http_ssl_module
    make -j `grep -c processor /proc/cpuinfo`&& make install
    if [ $? -ne 0 ];then
        echo Install nginx is failed!
        exit 10 
    else
        echo "Install nginx is finished!" 
    fi
    cat > /lib/systemd/system/nginx.service <<EOF
[Unit]
Description=The nginx HTTP and reverse proxy server
After=network.target remote-fs.target nss-lookup.target

[Service]
Type=forking
ExecStart=${INSTALL_DIR}/sbin/nginx

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable --now nginx &> /dev/null 
    systemctl is-active nginx &> /dev/null ||  { color "nginx 启动失败,退出!" 1 ; exit; }
    color "nginx 安装完成" 0
    echo "<h1>welcome to M49 nginx website </h1>" > ${INSTALL_DIR}/html/index.html
}

install_nginx
