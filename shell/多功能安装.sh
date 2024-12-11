写一个自动安装考试系统的脚本，要求如下：
1、使用函数完成相关功能
2、按下a键可以实现：关闭firewalld防火墙和selinux
3、按下b键可以实现：判断是否更换yum源，如果没有更换，则替换现有centos源，下载阿里云/腾讯云yum源（如果已经更换则不下载）
4、按下c键可以实现：安装java环境
5、按下d键可以实现：安装mysql环境（可以是yum安装，也可以是二进制/编译安装，看自己）
6、按下e键可以实现：安装tomcat
7、按下f键可以实现：部署考试系统，并完成配置（修改配置文件：sed -ri.bak  's#jdbc.password=root#jdbc.password=QianFeng@123#g'  config.properties）
8、按下g键可以实现：启动考试系统（提示：重启tomcat即可启动考试系统）
9、按下q键可以实现：退出当前脚本


#!/bin/bash
#source执行
#使用函数完成自动部署考试系统
#关闭firewalld
close_firewalld(){
	systemctl status firewalld
	if [[ $? -ne 0 ]]; then
		#statements
		systemctl disabled --now firewalld
		echo "firewalld already closed"
	else
	    echo "firewalld has already been closed"	
	fi	
}

#关闭selinux
close_selinux(){
	setenforce 0 
sed -i '/SELINUX/{s/enforcing/disabled/}' /etc/selinux/config
      echo "selinux has already been closed"
}

change_yum_source(){
#换源
yum -y install wget
echo "default ali  "
#换阿里云
wget -O /etc/yum.repos.d/CentOS-Base.repo https://mirrors.aliyun.com/repo/Centos-7.repo
#换腾讯云
#wget -O /etc/yum.repos.d/CentOS-Base.repo https：//mirrors.cloud.tencent.com/repo/centos7_base.repo
}

install_java_binary(){
#安装java环境
#下载
wget http://10.36.106.254/soft/jdk-8u211-linux-x64.tar.gz
#解压
tar -zxvf jdk-8u211-linux-x64.tar.gz  -C /home/
mv /home/jdk1.8.0_211 /home/java
#配置环境变量
echo 'JAVA_HOME=/home/java
PATH=$JAVA_HOME/bin:$PATH
export JAVA_HOME PATH' > /etc/profile.d/jdk.sh
source /etc/profile
java && javac
if [[ $? == 0 ]]; then
	echo "java is installed successfully"
else 
	echo "error eccured in java installing "
fi
}


#安装mysql (yum 方式)
install_mysql_yum(){
echo "即将开始yum安装，确认已开启代理工具后按1开始，按任意键退出"
read user_input
if [[ $user_input == 1 ]]; then
   wget https://dev.mysql.com/get/mysql80-community-release-el7-7.noarch.rpm
   yum -y install mysql80-community-release-el7-7.noarch.rpm
   yum -y install yum-utils 
   #配置版本 此处使用5.7版本 禁用8.0版本
   yum-config-manager --enable mysql57-community
   yum-config-manager --disable mysql80-community
   #安装mysql server
   yum install -y mysql-community-server
   #启动服务
   systemctl start mysqld
      if [[ $? == 0 ]]; then
	    #定义密码
        my_passwd=`grep password /var/log/mysqld.log | awk -F: '{print $4}'`
        echo "安装完成，及时修改密码"
        echo "初始密码为$my_passwd"
      else
         echo "安装失败 请重试" 
      fi       
else
	exit
fi
}

#安装tomcat
install_tomcat_binary(){
   wget http://10.36.106.254/soft/apache-tomcat-8.5.83.tar.gz
   tar -xzvf apache-tomcat-8.5.83.tar.gz  -C /usr/local/
   mv /usr/local/apache-tomcat-8.5.83/ /usr/local/tomcat
   echo 'CATALINA_HOME=/usr/local/tomcat
         export CATALINA_HOME' > /etc/profile.d/tomcat.sh
   source  /etc/profile     
}

#安装考试系统
install_tomexam(){
	yum -y install zip unzip
	wget http://10.36.106.254/soft/TomExam.zip
	unzip TomExam.zip
	
}
#部署tomexam
config_tomexam(){
	#配置properties文件
	cp -r TomExam/ROOT /usr/local/tomcat/webapps
	sed -ri.bak  's#jdbc.password=root#jdbc.password=QianFeng@123#g'  /usr/local/tomcat/webapps/ROOT/WEB-INF/classes/config.properties
    #跑sql脚本
    mysql -u root -p'QianFeng@123'  -D tomexam3_free < /root/TomExam/tomexam3_free.sql
}

#启动tomcat
start_tomcat(){
	source /usr/local/tomcat/bin/startup.sh
}

echo '-------------------------------------------------
      | 按下a键可以实现：关闭firewalld防火墙和selinux    |
      |          按下b键可以实现：更换yum源              |
      |         按下c键可以实现：安装java环境            |
      |         按下d键可以实现：安装mysql环境           |
      |         按下e键可以实现：安装tomcat              |
      |         按下f键可以实现：部署考试系统             |
      |         按下g键可以实现：启动考试系统             |
      |         按下q键可以实现：退出当前脚本             |
      -------------------------------------------------- '
read func_input
case $func_input in
	a )
    close_firewalld
    close_selinux
		;;
	b )
    change_yum_source
        ;;
    c )
    install_java_binary
       ;;
    d )
    install_mysql_yum
       ;;
    e )
    install_tomcat_binary
       ;;
    f )
    install_tomexam
    config_tomexam
      ;;
     g )
     start_tomcat
      ;;
      q )
      exit
      ;;      
esac