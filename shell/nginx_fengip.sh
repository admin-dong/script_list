#!/bin/bash

# 配置参数
LOG_FILE="/var/log/nginx/access.log"  # Nginx日志路径
THRESHOLD=100  # 访问次数超过此数值的IP将被封禁
EMAIL="your-email@example.com"  # 告警邮件接收地址

# 统计并获取需要封禁的IP列表
BLOCK_IPS=$(grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" $LOG_FILE | sort | uniq -c | sort -nr | awk -v limit=$THRESHOLD '$1 > limit {print $2}')

# 封禁IP，并记录要发送的邮件内容
MAIL_CONTENT="The following IPs have been blocked due to exceeding the access threshold of ${THRESHOLD} times:\n"
for ip in $BLOCK_IPS; do
    iptables -A INPUT -s $ip -j DROP
    MAIL_CONTENT="${MAIL_CONTENT}\n$ip"
done

# 如果有需要封禁的IP，则发送告警邮件
if [ -n "$BLOCK_IPS" ]; then
    echo -e "$MAIL_CONTENT" | mail -s "IP Blocking Alert" $EMAIL
fi