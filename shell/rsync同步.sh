#!/bin/bash


if  [ $# -ne 1 ];then
   echo "仅支持一个路径参数."
   exit
fi 

# 判断文件是否存在
if [ ! -e $1 ];then
    echo "[ $1 ] dir or file not find!"
    exit
fi

# 获取父路径
fullpath=`dirname $1`

# 获取子路径
basename=`basename $1`

# 进入到父路径
cd $fullpath

for ((host_id=102;host_id<=103;host_id++))
  do
    # 使得终端输出变为绿色
    tput setaf 2
    echo ===== elk${host_id}.oldboyedu.com: $basename =====
    # 使得终端恢复原来的颜色
    tput setaf 7
    # 将数据同步到其他两个节点
    rsync -az $basename  `whoami`@elk${host_id}.oldboyedu.com:$fullpath
    if [ $? -eq 0 ];then
      echo "命令执行成功!"
    fi
done

