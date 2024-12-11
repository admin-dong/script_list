#!/bin/bash
#author zed
#desc 备份配置文件


#1.vars
ip=`hostname -I |awk  '{print $1}'`
time=`date +%F_%w`
backup_dir=/bachup/$ip


#2.备份
mkdir -p $backup_dir
tar zcf $backup_dir/conf-$time.tar.gz /etc/ /var/spool/cron/


#3.推送
rsync -a /backup/  rsync_backup@192.168.1.100::backup  --password-file=/etc/clint.client

#4.清理
find $backup_dir -type f -name "*.tar.gz" -mtime +7  |xargs rm -f




#!/bin/bash
#author zed
#desc 备份服务器文件


#1.vars
ip=`hostname -I |awk  '{print $1}'`
time=`date +%F_%w`
backup_dir=/bachup/${ip}
backup_server=192.168.1.100
backup_file=conf-$time.tar.gz


#2.备份
mkdir -p ${backup_dir}
tar zcf ${backup_dir}/${backup_file}  /etc/ /var/spool/cron/


#3.推送
rsync -a ${backup_dir}  rsync_backup@${backup_server}::backup  --password-file=/etc/clint.client

#4.清理
find ${backup_dir} -type f -name "*.tar.gz" -mtime +7  |xargs rm -f





#!/bin/bash
#author zed
#desc 检查备份 清理旧备份


#-。清理旧的备份
find /backup -type f -name "*.tar.gz" -mtime+180 |xarges rf -f
#1.统计备份结果
find /backup/ -type f -name "*.tar.gz" |xarges  \
ls -lhd | \
awk -F'[ /]+' 'BEGIN{print "ip地址","备份文件名字","大小"} {print $(NF-1),$NF,$5}' | \
colunm -t >/server/scripts/result.txt

#2.发送备份结果到指定邮箱
cat /server/scripts/result.txt | mail -s "备份报告" 123456@qq.com



#!/bin/bash
#author zed
#desc 检查备份 清理旧备份

#-。清理旧的备份
find /backup -type f -name "*.tar.gz" -mtime+180 | xargs rm -f

#1.统计备份结果
result_file="/server/scripts/result.txt"
find /backup/ -type f -name "*.tar.gz" | xargs ls -lhd | awk -F'[ /]+' 'BEGIN{print "IP地址","备份文件名","大小"} {print $(NF-1),$NF,$5}' | column -t > "$result_file"

#2.将备份结果发送到飞书Webhook机器人
feishu_webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_FEISHU_WEBHOOK_URL_HERE"

# 读取result.txt内容并发送到飞书
message=$(cat "$result_file")
json="{\"msg_type\": \"text\", \"content\": {\"text\": \"$message\"}}"

curl -X POST -H 'Content-Type: application/json' -d "$json" "$feishu_webhook_url"