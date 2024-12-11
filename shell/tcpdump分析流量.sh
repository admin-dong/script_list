#!/bin/bash
################

if [ $# -ne 2 ];then
    echo "usage: $0 网卡 抓包时间"
    exit -1
fi

tcpdump --version > /dev/null

if [ $? -ne 0 ];then
    yum install tcpdump -y
fi

firstCard=""

function net() {

    if [ $(ip addr | grep inet | grep ppp | wc -l) -gt 0 ]; then
        ip r | grep ppp | grep -v default|awk '{print $NF}' > /tmp/ppp_ip
        firstCard=$(ip r|grep ppp| grep -v default| awk '{print $3}' | head -n 1)
    elif [ $(ip addr | grep inet | grep wan | wc -l) -gt 0 ]; then
        ip r | grep wan | grep -v default | awk '{print $9}' > /tmp/ppp_ip
        firstCard=$(ip r|grep wan | grep -v default | awk '{print $3}' | head -n 1)
    else
        ip route | grep default | awk '{print $3}' > /tmp/ppp_ip
        firstCard=$(ip route | grep default | awk '{print $5}' | head -n 1)
    fi

}

net

    
echo "本机省份 ：$(curl -s --interface $firstCard myip.ipip.net)" > /root/province_percentage_res




timeout $2 tcpdump -i $1 -n |grep -v -E 'IP6|Broadcast'|grep length > /tmp/tcpdump_tmp
cat /tmp/tcpdump_tmp | awk -F'>' '{print $2}' > /tmp/tcpdump_tmp_tmp
cat /tmp/tcpdump_tmp_tmp|awk -F: '{print $1}'|awk -F. 'BEGIN {OFS="."} {print $1,$2,$3,$4}' > /tmp/tcpdump_tmp_tmp_ip
cat /tmp/tcpdump_tmp_tmp|awk '{print $NF}' > /tmp/tcpdump_tmp_tmp_length
paste /tmp/tcpdump_tmp_tmp_ip /tmp/tcpdump_tmp_tmp_length|grep -v -E "$(cat /tmp/ppp_ip|sed ':a;N;$!ba;s/\n/|/g')|100.|192.|127.|id|length"|awk '{sum[$1]+=$2}END{for(i in sum){print i,sum[i]}}' > /tmp/tcpdump_ip_length
cat /tmp/tcpdump_ip_length|shuf|tail -5000 > /tmp/tcpdump_ip_length_tmp
sed -n 1,1000p /tmp/tcpdump_ip_length_tmp > /tmp/tcpdump_ip_length_tmp_1_1000
sed -n 1001,2000p /tmp/tcpdump_ip_length_tmp > /tmp/tcpdump_ip_length_tmp_1001_2000
sed -n 2001,3000p /tmp/tcpdump_ip_length_tmp > /tmp/tcpdump_ip_length_tmp_2001_3000
sed -n 3001,4000p /tmp/tcpdump_ip_length_tmp > /tmp/tcpdump_ip_length_tmp_3001_4000
sed -n 4001,5000p /tmp/tcpdump_ip_length_tmp > /tmp/tcpdump_ip_length_tmp_4001_5000



touch /tmp/tcpdump_province_length
cat /dev/null > /tmp/tcpdump_province_length
for item in "/tmp/tcpdump_ip_length_tmp_1_1000" "/tmp/tcpdump_ip_length_tmp_1001_2000" "/tmp/tcpdump_ip_length_tmp_2001_3000" "/tmp/tcpdump_ip_length_tmp_3001_4000" "/tmp/tcpdump_ip_length_tmp_4001_5000";do
    {
        IFS=$'\n'
        for i in `cat $item`;do
            if [ x"$i" != x"" ];then
                echo ""$(echo "$(curl -s http://xxxxxxx/ipip/`echo ${i}|awk '{print $1}'`|jq .ipip|jq .province)"|grep -v -E '共享地址|局域网|本机地址|保留地址'|tr -d '"')" `echo ${i}|awk '{print $2}'`" >> /tmp/tcpdump_province_length
            fi
        done
    }&
done
wait




cat /tmp/tcpdump_province_length|awk '{sum[$1]+=$2}END{for(i in sum){print i,sum[i]}}' > /tmp/tcpdump_everyprovince_everylength
data=`cat /tmp/tcpdump_everyprovince_everylength|sort -n`
all_num=$(awk '{ sum += $2 } END { print sum }' /tmp/tcpdump_everyprovince_everylength)
IFS=$'\n'
for i in $data;do
    num_item_province=$(echo $i|awk '{print $2}')
    item_province=$(echo $i|awk '{print $1}')
    percentage=$(awk "BEGIN {printf \"%.3f\", ${num_item_province}/${all_num} * 100}")
    echo -e "${item_province}\t:${percentage}%" >> /root/province_percentage_res
done


cat /root/province_percentage_res