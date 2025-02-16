#!/bin/bash
touch 1.txt
file=1.txt
echo -e "分析一个月SSH成功登录情况:\n"
cat secure* |grep Accepted | awk '{print $11,$9,$1,$2,$3}'>$file

while IFS= read -r line; do
    # 使用制表符\t对齐输出
    echo -e "\tIP:$(echo $line | awk '{print $1}')\t用户: $(echo $line | awk '{print $2}')\t$(echo $line | awk '{print $3 " " $4 " " $5}')\t登录成功"
done < "$file"

touch 2.txt
file2=2.txt
echo -e "\n分析一个月SSH暴力破解来源IPTop10:\n"
cat secure* |grep "Failed password for invalid" | awk '{print $11,$13}'>$file
cat secure* |grep "Failed password for" |grep -v "invalid" |awk '{print $9,$11}'>>$file
cat $file |awk '{print $2}'|sort |uniq -c |sort -nr |head -n 10 |awk '{print $2,$1}'>$file2
while IFS= read -r line; do
    # 使用制表符\t对齐输出
    echo -e "\t用户IP:$(echo $line | awk '{print $1}')\t暴力破解:$(echo $line | awk '{print $2}')次"
done < "$file2"


touch 3.txt
file3=3.txt
echo -e "\n分析一个月 SSH 被暴力破解用户 Top10:\n"
cat secure* |grep "Failed password for invalid" | awk '{print $11,$13}'>$file
cat secure* |grep "Failed password for" |grep -v "invalid" |awk '{print $9,$11}'>>$file
cat $file |awk '{print $1}'|sort |uniq -c |sort -nr |head -n 10 |awk '{print $2,$1}'>$file3
while IFS= read -r line; do
    # 使用制表符\t对齐输出
    echo -e "\t用户IP:$(echo $line | awk '{print $1}')\t暴力破解:$(echo $line | awk '{print $2}')次"
done < "$file3"



##之前写的
##优化之后的 
#!/bin/bash
echo -e "分析一个月SSH成功登录情况:\n"
cat secure* |grep Accepted | awk '{print"\tIP:"$11,"\t用户:"$9,"\t"$1,$2,$3 "\t登录成功"}'
echo -e "\n分析一个月SSH暴力破解来源IPTop10:\n"
cat secure* |grep "Failed password " | awk '{print $(NF-3)}'  |sort |uniq -c |sort -nr |head -n 10 | awk '{print "\t异常IP: "$2 "\t暴力破解:"$1"次"}'
echo -e "\n分析一个月 SSH 被暴力破解用户 Top10:\n"
cat secure* |grep "Failed password " | awk '{print $(NF-5)}'| sort | uniq -c |sort -rn | head -n 10 | awk '{print "\t用户: "$2 "\t暴力破解 "$1"次"}'
