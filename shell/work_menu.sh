#!/bin/bash

echo -en "\E[$[RANDOM%7+31];1m"
cat <<EOF
请选择：
1）备份数据库
2）清理日志
3）软件升级
4）软件回滚
5）删库跑路
EOF
echo -en '\E[0m'

read -p  "请输入上面数字1-5: " MENU

case $MENU in
1)
   echo "执行备份数据库"
   #./backup.sh
   ;;
2)
    echo "清理日志"
    ;;
3)
    echo "软件升级"
    ;;
4)
    echo "软件回滚"
    ;;
5)
    echo "删库跑路" 
    ;;
*)
    echo "INPUT FALSE!"
esac
