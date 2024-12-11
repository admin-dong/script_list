#！/bin/bash
#0.vars 
tmp_file=/server/files/res.txt
log_file=/server/files/access.log
#1. 分析日志
awk '{print $1}'  $log_file |sort |uniq -c |sort -rn 
|head -5 >$tmp_file

#2. 读取文件
while read line 
do
     cnt=`echo $line|awk '{print $1}'`
     ip=`echo $line|awk '{print $2}'`
     echo "ip地址:$ip,访问次数$cnt"
     if_drop=`iptables -nL |grep -w "$ip" |wc -l`
     if [ $cnt -ge 200 -a $if_drop -eq 0 ];then
         iptables -t filter -I INPUT  -s $ip   -j 
DROP
     fi

     done <$tmp_file


# 文件的每一行的 第1列 赋值给count变量 
# 文件的每一行的 第2列 赋值给ip变量 

while read count ip
do
echo "ip地址是$ip 访问次数是$count"
done<$result_file
