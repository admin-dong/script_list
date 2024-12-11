#!/bin/sh

JAVA_HOME=/apps/svr/jdk1.8
APP_NAME=dwadawdwa-1.0.0.jar
ENV=sit

APP_HOME=$(dirname $(cd `dirname $0`; pwd))
URANDOM=-Djava.security.egd=file:/dev/./urandom

psid=0
bakfile() {
#保留文件数

ReservedNum=3

#当前脚本所在目录

RootDir=$(cd `dirname $0`; cd ../bak; pwd)

#显示文件数， *.*可以改为指定文件类型

FileNum=$(cd `dirname $0`;cd ../bak;ls -l *.tar.gz* | grep ^- | wc -l)

while(( $FileNum > $ReservedNum ))

do

    #取最旧的文件，*.*可以改为指定文件类型

    OldFile=$(cd `dirname $0`;cd ../bak;ls -rt *.* | head -1)

    echo "Delete File:"$RootDir'/'$OldFile

    rm -f $RootDir'/'$OldFile

    let "FileNum--"

done
}
checkpid() {
   ps=`ps -ef | grep $APP_HOME/$APP_NAME | grep -v grep`
   if [ -n "$ps" ]; then
      psid=`echo $ps | awk '{print $2}'`
   else
      psid=0
   fi
}
start() {
   checkpid
   if [ $psid -ne 0 ]; then
      echo "================================"
      echo "warn: $APP_NAME already started! (pid=$psid)"
      echo "================================"
   else
      echo -n "Starting $APP_NAME ..."
      cd $APP_HOME
      nohup $JAVA_HOME/bin/java -Xms512m -Xmx1024m $URANDOM -jar $APP_HOME/$APP_NAME --spring.profiles.active=$ENV >/dev/null 2>&1 &

      checkpid
      if [ $psid -ne 0 ]; then
         echo "(pid=$psid) [OK]"

         # startup and backup
         if [ ! -d 'bak' ]; then
           mkdir bak
         fi

         echo -n "Backuping $APP_NAME to ./bak/$APP_NAME.`date +%Y%m%d%H%M%S`.tar.gz ..."
         bakfile
         tar -zcf ./bak/$APP_NAME.`date +%Y%m%d%H%M%S`.tar.gz $APP_NAME
         echo "[OK]"
      else
         echo "[Failed]"
      fi
   fi
}
stop() {
   checkpid
   if [ $psid -ne 0 ]; then
      echo -n "Stopping $APP_NAME ...(pid=$psid) "
      kill -9 $psid
      if [ $? -eq 0 ]; then
         echo "[OK]"
      else
         echo "[Failed]"
      fi

      checkpid
      if [ $psid -ne 0 ]; then
         stop
      fi
   else
      echo "================================"
   fi
}


case "$1" in
   'start')
      start
      ;;
   'stop')
     stop
     ;;
   'restart')
     stop
     start
     ;;
   'status')
     status
     ;;
   'info')
     info
     ;;
  *)
     echo "Usage: $0 {start|stop|restart}"
     exit 1
esac
exit 0


#根据传入的第一个参数执行相应的操作：
# start: 启动应用。
# stop: 停止应用。
# restart: 先停止再启动应用。
# status: 查看应用的状态（这里没有实现）。
# info: 显示应用信息（这里没有实现）。
# 如果传入的参数不正确，输出使用帮助信息并退出。
