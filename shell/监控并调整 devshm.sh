#!/bin/bash

# 加载 /etc/profile 中的环境变量设置
source /etc/profile

# 设置调试模式（显示命令及其参数）
set -x

# 获取物理内存的总大小（单位：字节）
mem_size=$(free -b | awk '{if($1=="Mem:")print$2}')

# 获取 /dev/shm 的大小（单位：字节）
shm_size=$(df -B1 /dev/shm | awk '{if($1=="tmpfs" && $NF=="/dev/shm")print$2}')

# 计算内存大小的40%
mem_size_4=$(( ${mem_size}*4/10 ))

# 计算内存大小的50%
mem_size_5=$(( ${mem_size}*5/10 ))

# 计算内存大小的60%
mem_size_6=$(( ${mem_size}*6/10 ))

# 如果 /dev/shm 的大小不在合理范围内，则重新挂载并调整大小
if [[ ${shm_size} -lt ${mem_size_4} ]] || [[ ${shm_size} -gt $(( ${mem_size_6} )) ]]; then
    echo "Adjusting /dev/shm size to ${mem_size_5} bytes."
    if mount -o remount,rw,size=$(( ${mem_size_5} )) --types tmpfs --source none --target /dev/shm; then
        echo "Successfully adjusted /dev/shm size."
    else
        echo "Failed to adjust /dev/shm size."
    fi
fi

#Bash脚本用于监控并调整 /dev/shm（共享内存文件系统）的大小