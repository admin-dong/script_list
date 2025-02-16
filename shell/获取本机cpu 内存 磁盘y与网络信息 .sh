y=`free -m |grep Mem |awk {'print $2'}`
#echo $y

x=`cat  /proc/cpuinfo | grep "cpu cores" | head -1 | awk -F ':' '{print $2}'`
#echo $x

z=`fdisk -l |grep  "Disk /dev/sd" | awk  '{print $3}'`
#echo $z
echo "本机CPU核心数是${x}，本机内存容量是${y}MB，本机磁盘容量是${z}GB。"



a=`ip -br a  |grep ens | awk '{print $3}' | awk -F '/' '{print $1}'`
#之前的 
b=`curl -s cip.cc |grep IP  | awk -F':' '{print $2}' |awk '{print $1}'`
#或者 
b=`curl -s ifconfig.me  
echo "本机内网1P地址是:${a}，本机访问互联网的出口IP地址是:${b} "


#如果是多终端显示的话 就是/etc/profile 里面添加上面的代码

#开机运行的
# 方法  1 （可以） 感觉这个最简单
# chmod +x /etc/rc.d/rc.local
# vim /etc/rc.d/rc.local
# cd /etc/init.d && sh time.sh
# 方法 2 （可以）（不建议  启动相关的）
# ln -s /etc/init.d/time.sh /etc/rc2.d/S99time.sh
# 方法3 （没跑通 ）（centos 6之前的 不推荐 ）
# 在脚本里面加参数 #chkconfig: 6 88 99 chkconfig  -add /etc下面文件 重启不生效 
# 方法4 （可以 ）
# systemctl 纳管
# systemctl enable time.service 
# 方法5 (可以 )
# crontab -e
# @reboot /bin/sh /etc/init.d/time.sh
