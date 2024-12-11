#!/bin/bash

# 遍历所有名为pai-ecdn*的Docker容器
for id in $(docker ps -f "name=pai" -q 2>/dev/null); do
    # 将主机上的/etc/hosts文件复制到每个容器的/tmp/目录
    docker cp /etc/hosts $id:/tmp/
    # 检查复制操作是否成功
    if [ $? -eq 0 ]; then
        # 在容器内将/tmp/hosts文件复制到/etc/hosts
        docker exec $id cp -f /tmp/hosts /etc/hosts
        # 清理临时文件
        docker exec $id rm -f /tmp/hosts
    fi
done