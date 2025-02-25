#!/bin/bash

menu(){
	while true ; do	
		echo -en "\E[$[RANDOM%7+31];1m"
		cat <<-EOF
		请选择需要功能，只支持centos7，rocky8，ununtu20.04：
		1） 关闭防火墙
		2） 关闭SElinux
		3)  配置网卡且默认名称为eth0
		4)  做1-3
		5） 配置yum源，apt源
		6） centos系列实现邮件通讯
		7） 时间同步
		8） centos系列自动挂载光盘，并追加光盘yum源
		9） centos系列装常用软件
		10）做5-10
		0）退出
		EOF
		echo -en '\E[0m'
		read -p "请选择你要做的操作:" menu
		case $menu  in 
			1)
				disable_firewalld
				;;
			2)
				disable_selinux
				;;
			3)
				change_eth0 

				;;
			4)	
				disable_firewalld
				disable_selinux
				change_eth0
				;;
			5)	
				set_yum
				;;
			6)
				set_mail
				;;
			7)
				set_ntp
				;;
			8)	
				set_autofs
				;;
			9)	
				commonsoft
				;;
			10)	
				
				set_yum 1
				set_mail
				set_ntp
				set_autofs
				commonsoft
				;;
			0|q|exit|quite)      
				exit
				;;
			*)echo "选择无效，请重选"
				;;
		esac
		done
}
release (){
	. /etc/os-release
	if [[ $ID =~ rocky|centos|ubuntu ]]; then
		echo "尊贵的 $ID 用户，您好"
	else
		echo "另请高明"
        	exit 
	fi
}
color () {
        RES_COL=60
        MOVE_TO_COL="echo -en \\033[${RES_COL}G"
        SETCOLOR_SUCCESS="echo -en \\033[1;32m"
        SETCOLOR_FAILURE="echo -en \\033[1;31m"
        SETCOLOR_WARNING="echo -en \\033[1;33m"
        SETCOLOR_NORMAL="echo -en \E[0m"
        echo -n "$1" && $MOVE_TO_COL
        echo -n "["
        if [ $2 = "success" -o $2 = "0" ] ;then
            ${SETCOLOR_SUCCESS}
            echo -n $"  OK  "    
        elif [ $2 = "failure" -o $2 = "1"  ] ;then
            ${SETCOLOR_FAILURE}
            echo -n $"FAILED"
        else
            ${SETCOLOR_WARNING}
            echo -n $"WARNING"
        fi
        ${SETCOLOR_NORMAL}
        echo -n "]"
        echo 
}

main(){
	
	release
	menu
       
}

disable_firewalld(){
	systemctl disable --now firewalld >& /dev/null
	color "防火墙关闭成功" 0 
}
disable_selinux(){
	while [[ $ID =~ rocky|centos ]] ;do
		sed -ri "/^SELINUX=/s/(SELINUX=).*/\1disabled/" /etc/selinux/config >& /dev/null
		color "SELINUX已关闭" 0
		break
	done
        while [[ $ID == ubuntu ]] ;do
                color "SELINUX默认未安装，无需更改" 2
                break
        done
}
set_yum(){
	if [[ $ID == rocky ]] ;then
		[ -d /etc/yum.repos.d/backup ] || mkdir /etc/yum.repos.d/backup 
		mv /etc/yum.repos.d/*.repo /etc/yum.repos.d/backup ;
		cat > /etc/yum.repos.d/base.repo <<EOF
[BaseOS]
name=BaseOS
baseurl=https://mirrors.aliyun.com/rockylinux/\$releasever/BaseOS/x86_64/os/
        http://mirrors.163.com/rocky/\$releasever/BaseOS/x86_64/os/
        https://mirrors.nju.edu.cn/rocky/\$releasever/BaseOS/x86_64/os/
        https://mirrors.sjtug.sjtu.edu.cn/rocky/\$releasever/BaseOS/x86_64/os/
        http://mirrors.sdu.edu.cn/rocky/\$releasever/BaseOS/x86_64/os/       
gpgcheck=0

[AppStream]
name=AppStream
baseurl=https://mirrors.aliyun.com/rockylinux/\$releasever/AppStream/x86_64/os/
        http://mirrors.163.com/rocky/\$releasever/AppStream/x86_64/os/
        https://mirrors.nju.edu.cn/rocky/\$releasever/AppStream/x86_64/os/
        https://mirrors.sjtug.sjtu.edu.cn/rocky/\$releasever/AppStream/x86_64/os/
        http://mirrors.sdu.edu.cn/rocky/\$releasever/AppStream/x86_64/os/
gpgcheck=0

[extras]
name=extras
baseurl=https://mirrors.aliyun.com/rockylinux/\$releasever/extras/\$basearch/os
        http://mirrors.163.com/rocky/\$releasever/extras/\$basearch/os
        https://mirrors.nju.edu.cn/rocky/\$releasever/extras/\$basearch/os
        https://mirrors.sjtug.sjtu.edu.cn/rocky/\$releasever/extras/\$basearch/os
        http://mirrors.sdu.edu.cn/rocky/\$releasever/extras/\$basearch/os 
       
gpgcheck=0
enabled=1

[PowerTools]
name=CentOS-\$releasever - PowerTools
baseurl=https://mirrors.aliyun.com/rockylinux/\$releasever/PowerTools/\$basearch/os/
        http://mirrors.163.com/rocky/\$releasever/PowerTools/\$basearch/os/
        http://mirrors.sdu.edu.cn/rocky/\$releasever/PowerTools/\$basearch/os/
        https://mirrors.sjtug.sjtu.edu.cn/rocky/\$releasever/PowerTools/\$basearch/os/
        http://mirrors.sdu.edu.cn/rocky/\$releasever/PowerTools/\$basearch/os/
gpgcheck=0
enabled=0


[epel]
name=EPEL
baseurl=https://mirror.tuna.tsinghua.edu.cn/epel/\$releasever/Everything/\$basearch
        https://mirrors.cloud.tencent.com/epel/\$releasever/Everything/\$basearch
        https://mirrors.huaweicloud.com/epel/\$releasever/Everything/\$basearch
        https://mirrors.aliyun.com/epel/\$releasever/Everything/\$basearch
gpgcheck=0
enabled=1
EOF
        	yum clean all >& /dev/null
		yum repolist  &> /dev/null
		yum makecache  
		[ $? -eq 0 ] && color "$ID yum源配置完成" 0 || color "$ID yum源配置失败，请查找原因" 1
	elif [[ $ID == centos ]] ;then
        	mkdir /etc/yum.repos.d/backup &> /dev/null
        	mv /etc/yum.repos.d/*.repo /etc/yum.repos.d/backup
        	cat > /etc/yum.repos.d/base.repo <<EOF
[base]
name=CentOS
baseurl=https://mirror.tuna.tsinghua.edu.cn/centos/\$releasever/os/\$basearch/
        https://mirrors.huaweicloud.com/centos/\$releasever/os/\$basearch/
        https://mirrors.cloud.tencent.com/centos/\$releasever/os/\$basearch/
        https://mirrors.aliyun.com/centos/\$releasever/os/\$basearch/
gpgcheck=0

[extras]
name=extras
baseurl=https://mirror.tuna.tsinghua.edu.cn/centos/\$releasever/extras/\$basearch
        https://mirrors.huaweicloud.com/centos/\$releasever/extras/\$basearch
        https://mirrors.cloud.tencent.com/centos/\$releasever/extras/\$basearch
        https://mirrors.aliyun.com/centos/\$releasever/extras/\$basearch
       
gpgcheck=0
enabled=1


[epel]
name=EPEL
baseurl=https://mirror.tuna.tsinghua.edu.cn/epel/\$releasever/\$basearch
        https://mirrors.cloud.tencent.com/epel/\$releasever/\$basearch/
        https://mirrors.huaweicloud.com/epel/\$releasever/\$basearch 
        https://mirrors.cloud.tencent.com/epel/\$releasever/\$basearch
        http://mirrors.aliyun.com/epel/\$releasever/\$basearch
gpgcheck=0
enabled=1
EOF
		 yum clean all >& /dev/null
                 yum repolist  &> /dev/null
		 yum makecache 
		 [ $? -eq 0 ] && color "$ID yum源配置完成" 0 || color "$ID yum源配置失败，请查找原因" 1
	elif [ $ID == ubuntu ]; then
		local source=$1
		[ -z $source ] && read -p "请输入要配置的源，1,阿里，2，清华，3，北大:" source || echo "配置默认源为阿里"
		case $source  in
			1)
				cat >/etc/apt/sources.list <<EOF
# See http://help.ubuntu.com/community/UpgradeNotes for how to upgrade to
# newer versions of the distribution.
deb https://mirrors.aliyun.com/ubuntu/ focal main restricted
# deb-src https://mirrors.aliyun.com/ubuntu/ focal main restricted

## Major bug fix updates produced after the final release of the
## distribution.
deb https://mirrors.aliyun.com/ubuntu/ focal-updates main restricted
# deb-src https://mirrors.aliyun.com/ubuntu/ focal-updates main restricted

## N.B. software from this repository is ENTIRELY UNSUPPORTED by the Ubuntu
## team. Also, please note that software in universe WILL NOT receive any
## review or updates from the Ubuntu security team.
deb https://mirrors.aliyun.com/ubuntu/ focal universe
# deb-src https://mirrors.aliyun.com/ubuntu/ focal universe
deb https://mirrors.aliyun.com/ubuntu/ focal-updates universe
# deb-src https://mirrors.aliyun.com/ubuntu/ focal-updates universe

## N.B. software from this repository is ENTIRELY UNSUPPORTED by the Ubuntu
## team, and may not be under a free licence. Please satisfy yourself as to
## your rights to use the software. Also, please note that software in
## multiverse WILL NOT receive any review or updates from the Ubuntu
## security team.
deb https://mirrors.aliyun.com/ubuntu/ focal multiverse
# deb-src https://mirrors.aliyun.com/ubuntu/ focal multiverse
deb https://mirrors.aliyun.com/ubuntu/ focal-updates multiverse
# deb-src https://mirrors.aliyun.com/ubuntu/ focal-updates multiverse

## N.B. software from this repository may not have been tested as
## extensively as that contained in the main release, although it includes
## newer versions of some applications which may provide useful features.
## Also, please note that software in backports WILL NOT receive any review
## or updates from the Ubuntu security team.
deb https://mirrors.aliyun.com/ubuntu/ focal-backports main restricted universe multiverse
# deb-src https://mirrors.aliyun.com/ubuntu/ focal-backports main restricted universe multiverse

## Uncomment the following two lines to add software from Canonical's
## 'partner' repository.
## This software is not part of Ubuntu, but is offered by Canonical and the
## respective vendors as a service to Ubuntu users.
# deb http://archive.canonical.com/ubuntu focal partner
# deb-src http://archive.canonical.com/ubuntu focal partner

deb https://mirrors.aliyun.com/ubuntu/ focal-security main restricted
# deb-src https://mirrors.aliyun.com/ubuntu/ focal-security main restricted
deb https://mirrors.aliyun.com/ubuntu/ focal-security universe
# deb-src https://mirrors.aliyun.com/ubuntu/ focal-security universe
deb https://mirrors.aliyun.com/ubuntu/ focal-security multiverse
# deb-src https://mirrors.aliyun.com/ubuntu/ focal-security multiverse
EOF
				apt clean all &>/dev/null
				apt update
				[ $? -eq 0 ] && color "$ID apt源配置完成" 0 || color "$ID apt源配置失败，请查找原因" 1
				;;
			2)
				 cat >/etc/apt/sources.list <<EOF
# 默认注释了源码镜像以提高 apt update 速度，如有需要可自行取消注释
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal main restricted universe multiverse
# deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-updates main restricted universe multiverse
# deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-updates main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-backports main restricted universe multiverse
# deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-backports main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-security main restricted universe multiverse
# deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-security main restricted universe multiverse

# 预发布软件源，不建议启用
# deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-proposed main restricted universe multiverse
# deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-proposed main restricted universe multiverse
EOF
				 apt clean all &>/dev/null
                                 apt update
                                 [ $? -eq 0 ] && color "$ID apt源配置完成" 0 || color "$ID apt源配置失败，请查找原因" 1

				;;
			3)
				cat >/etc/apt/sources.list <<EOF
deb https://mirrors.cloud.tencent.com/ubuntu/ focal main restricted universe multiverse
deb-src https://mirrors.cloud.tencent.com/ubuntu/ focal main restricted universe multiverse

deb https://mirrors.cloud.tencent.com/ubuntu/ focal-security main restricted universe multiverse
deb-src https://mirrors.cloud.tencent.com/ubuntu/ focal-security main restricted universe multiverse

deb https://mirrors.cloud.tencent.com/ubuntu/ focal-updates main restricted universe multiverse
deb-src https://mirrors.cloud.tencent.com/ubuntu/ focal-updates main restricted universe multiverse

deb https://mirrors.cloud.tencent.com/ubuntu/ focal-backports main restricted universe multiverse
deb-src https://mirrors.cloud.tencent.com/ubuntu/ focal-backports main restricted universe multiverse

## Not recommended
# deb https://mirrors.cloud.tencent.com/ubuntu/ focal-proposed main restricted universe multiverse
# deb-src https://mirrors.cloud.tencent.com/ubuntu/ focal-proposed main restricted universe multiverse
EOF
	 			apt clean all &>/dev/null
                                apt update
                                [ $? -eq 0 ] && color "$ID apt源配置完成" 0 || color "$ID apt源配置失败，请查找原因" 1

				;;
			*)	
				echo "weqweqweqw"
				;;
		esac
	else
		echo "无能为力" 
		exit
	fi
}
change_eth0(){
	while [[ $ID =~ rocky|centos ]] ;do
		grep "net.ifnames=0 biosdevname=0" /etc/default/grub >& /dev/null
		if [ $? -eq 0 ] ; then
                        color "$ID 网卡默认名称改过了，不要再改了" 2
                else
                        sed -ri "/^GRUB_CMDLINE_LINUX=/s/^(.*)\"/\1 net.ifnames=0 biosdevname=0\"/" /etc/default/grub;
                        grub2-mkconfig -o /boot/grub2/grub.cfg &>/dev/null
                        color "网卡默认名称修改成功" 0
                fi
		ethfilename=ifcfg-`ifconfig | sed -rn  "1s/^(.*):.*/\1/p"`
		ipaddr=`hostname -I |awk '{print $1}'`
		\rm /etc/sysconfig/network-scripts/${ethfilename}
		cat > /etc/sysconfig/network-scripts/ifcfg-eth0 <<-EOF
		NAME=con-eth0
		DEVICE=eth0
		IPADDR=${ipaddr}
		PREFIX=24
		GATEWAY=10.0.0.2
		DNS1=10.0.0.2
		DNS2=8.8.8.8
		DNS3=180.76.76.76
		ONBOOT=yes
		EOF
                color "网卡配置成功,重启生效" 0
		break;

	done
	while [[ $ID == ubuntu ]] ;do
		grep "net.ifnames=0 biosdevname=0" /etc/default/grub >& /dev/null
		if [ $? -eq 0 ] ; then 
		       	color "$ID 网卡默认名称改过了，不要再改了" 2 
		else
                	sed -ri "/^GRUB_CMDLINE_LINUX=/s/^(.*)\"/\1 net.ifnames=0 biosdevname=0\"/" /etc/default/grub;
               		update-grub  &> /dev/null;
			color "网卡默认名称修改成功" 0
		fi
                ethfilename=ifcfg-`ifconfig | sed -rn  "1s/^(.*):.*/\1/p"`
                ipaddr=`hostname -I |awk '{print $1}'`
		cat >/etc/netplan/00-installer-config.yaml <<EOF
# This is the network config written by 'subiquity'
network:
        ethernets:
                eth0:
                        dhcp4: no
                        addresses: [${ipaddr}/24]
                        gateway4: 10.0.0.2
                        nameservers:
                                addresses: [10.0.0.2,8.8.8.8,180.76.76.76]

        version: 2
EOF
		color "网卡配置成功,重启生效" 0
		break
	done

}
set_mail(){
	if  [[ $ID =~ rocky|centos ]] ;then
		rpm -q postfix &> /dev/null && color "postfix 已安装，请勿重复操作" 2 || { yum -y install postfix &> /dev/null ;systemctl enable --now postfix &>/dev/null;color "postfix 已安装" 0; }
 		rpm -q mailx &> /dev/null  && color "mailx 已安装，请勿重复操作" 2 || { yum -y install mailx &> /dev/null;color "mailx 已安装" 0; }
		color "邮件通讯功能已安装，想发邮件自己去配置 ~/.mailrc" 0
	else
		color "ubuntu 不会配邮件 会的教我" 2
 	fi
}
set_autofs(){
        if  [[ $ID =~ rocky|centos ]] ;then
                rpm -q autofs &> /dev/null && { color "autofs 已安装，请勿重复操作" 2 ; systemctl start autofs;} || { yum -y install autofs &> /dev/null ;systemctl enable --now autofs;color "autofs 已安装" 0; }
			while [ $ID = rocky ] ;do
				[[ `awk 'NR==3' /etc/yum.repos.d/base.repo` =~ "baseurl=http" ]] && { sed -ri.bak "3s#(baseurl=)(http.*)#\1file:///misc/cd/BaseOS\\n\\t\2#" /etc/yum.repos.d/base.repo; sed -ri.bak "13,15s#(baseurl=)(http.*)#\1file:///misc/cd/AppStream\\n\\t\2#" /etc/yum.repos.d/base.repo ;yum clean all &>/dev/null;yum makecache; color "追加光盘yum源成功" 0;} || color "yum源已经追加，或配置与本程序不同" 2 
		
			break
			done
                	while [ $ID = centos ] ;do
                        	[[ `awk 'NR==3' /etc/yum.repos.d/base.repo` =~ "baseurl=http" ]] && { sed -ri.bak "3s#(baseurl=)(http.*)#\1file:///misc/cd\\n\\t\2#" /etc/yum.repos.d/base.repo; yum clean all &>/dev/null;yum makecache; color "追加光盘yum源成功" 0; }|| color "yum源已经追加，或配置与本程序不同" 2

               		break
                	done
		
        else
                color "ubuntu 不会配autofs" 2
        fi
}
set_ntp(){
	stat=`systemctl is-active chronyd`
	while [[ $ID =~ rocky|centos ]] ;do
		if  [ "$stat" = active ] ;then
                	color "时间同步已经设置，请勿重复设置" 2

        	else
               		yum -y remove chrony &> /dev/null 
               		yum -y install chrony &>/dev/null || { color "chrony 安装失败，请检查yum源" 1 ; exit; }
               		sleep 3
                	sed  -ri  "3s/(server).*/\1 ntp1.aliyun.com iburst/" /etc/chrony.conf
                	sed  -ri  "4s/(server).*/\1 s1a.time.edu.cn iburst/" /etc/chrony.conf
                	sed  -ri  "5s/(server).*/\1 s1b.time.edu.cn iburst/" /etc/chrony.conf
                	sed  -ri  "6s/(server.*)/\\t/" /etc/chrony.conf
                	timedatectl set-timezone Asia/Shanghai
                	systemctl start chronyd &>/dev/null
                	systemctl enable chronyd &>/dev/null
                	systemctl is-active chronyd &>/dev/null 
                	[ $?==0  ] && color " 时间同步设置完成" 0 || color "时间同步设置失败" 1

        	fi
		break
        done
        while [[ $ID == ubuntu ]] ;do
		if  [ "$stat" = active ] ;then
                        color "时间同步已经设置，请勿重复设置" 2

                else
                        apt -y purge chrony &> /dev/null 
 			apt update &>/dev/null
                        apt -y install chrony &>/dev/null || { color "chrony 安装失败，请检查yum源" 1 ; exit; }
                        sleep 3
                        sed  -ri  "17s/(pool).*/\1 ntp1.aliyun.com iburst maxsources 4/" /etc/chrony/chrony.conf
                        sed  -ri  "18s/(pool).*/\1 s1a.time.edu.cn iburst maxsources 1/" /etc/chrony/chrony.conf
                        sed  -ri  "19s/(pool).*/\1 s1b.time.edu.cn iburst maxsources 1/" /etc/chrony/chrony.conf
                        sed  -ri  "20s/(pool.*)/\\t/" /etc/chrony/chrony.conf
                        timedatectl set-timezone Asia/Shanghai
                        systemctl start chronyd &>/dev/null
                        systemctl enable chronyd &>/dev/null
                        systemctl is-active chronyd &>/dev/null
                        [ $?==0  ] && color " 时间同步设置完成" 0 || color "时间同步设置失败" 1
                fi

                break
        done



}
commonsoft(){
	while [[ $ID =~ rocky|centos ]] ;do
		declare -a software
		software=( "bash-completion" 
			   "psmisc" 
			   "lrzsz"  
			   "tree" 
			   "man-pages" 
			   "redhat-lsb-core" 
			   "zip" 
			   "unzip" 
			   "bzip2" 
			   "wget" 	
			   "tcpdump"
			   "ftp" 
			   "rsync" 
			   "vim" 
			   "lsof"
				)
		for i in ${software[@]}
		do
		rpm -q $i &> /dev/null  && color "$i 已经安装，无需操作" 2 || { yum -y install $i &> /dev/null ; color "$i 安装成功" 0;}
		done
	
	break
	done
}
main


