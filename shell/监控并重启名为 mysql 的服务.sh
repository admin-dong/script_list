#!/bin/bash

# 加载 /etc/profile 中的环境变量设置
source /etc/profile

# 检查 mysql 服务是否已启用
if [[ ! -f /etc/systemd/system/multi-user.target.wants/mysql ]]; then
    echo "mysql not set enable"
    exit 0
fi

# 检查 mysql 服务是否正在运行
if [[ $(ps --no-headers -fC mysql | wc -l) -le 0 ]]; then
    echo "mysql not running..."
    exit 0
fi

# 获取当前的时间戳
nowtimestamp=$(date +%s)

# 获取 mysql 日志的最后一行
lastlogline=$(tail -n100 /var/log/mysql.log | grep -P '\[2[0-9]{3}-[0-9]{2}-[0-9]{2} \[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}' | tail -n1)
# 提取日志时间
lastlogtime=${lastlogline:1:19}

# 如果没有找到有效的时间戳，则设为0
if [[ "${lastlogtime}" == "" ]]; then
    lastlogtimestamp=0
else
    # 将日志时间转换为时间戳
    lastlogtimestamp=$(date -d "${lastlogtime}" +%s)
fi

# 记录当前时间和最后的日志时间
echo "[$(date +%FT%T)] lastlogtime: ${lastlogtime}" >> /var/log/mysql_logcheck.log

# 计算当前时间戳和最后一个日志时间戳之间的差值
let difftimestamp=${nowtimestamp}-${lastlogtimestamp}

# 如果两个时间戳之间的时间差大于600秒（10分钟），则重启 mysql 服务
if [[ ${difftimestamp} -gt 600 ]]; then
    systemctl restart mysql
fi