#!/bin/bash

. /etc/os-release
TIMEDATE=Asia/Shanghai 

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



firewall_disable () {
    systemctl disable --now firewalld &> /dev/null
	[ $? -eq 0 ] && color "防火墙关闭成功!" 0 || color "防火墙关闭失败!" 1
}


selinux_disabled (){
    sed -ri.bak 's/^(SELINUX=).*/\1disabled/' /etc/selinux/config
	[ $? -eq 0 ] && color "SElinux关闭成功!" 0 || color "SElinux关闭失败!" 1
	setenforce 0 &> /dev/null
}

iso_mount () {
    yum -y install autofs &> /dev/null
	[ $? -eq 0 ] && color "autofs安装成功!" 0 || color "安装失败，请检查yum仓库!" 1 
    systemctl enable --now autofs &> /dev/null
	[ $? -eq 0 ] && color "进入/misc/cd即完成挂载" 2

}

ubuntu_firewall_mask () {
    systemctl mask firewalld &> /dev/null
	[ $? -eq 0 ] && color "防火墙关闭成功!" 0 || color "防火墙关闭失败!" 1
}

ubuntu_iso_mount () {
    { apt update ; apt -y install autofs ; } &> /dev/null
	[ $? -eq 0 ] && color "autofs安装成功!" 0 || color "安装失败，请检查apt仓库!" 1
    systemctl enable --now autofs &> /dev/null
	[ $? -eq 0 ] && color "进入/misc/cd即完成挂载" 2

}

ubuntu_timedate () {
    timedatectl set-timezone $TIMEDATE
	[ $? -eq 0 ] && color "时区修改为$TIMEDATE成功!" 0 || color "时区修改为$TIMEDATE失败，请检查变量 (TIMEDATE)!" 1
}

ubuntu_root_ssh () {
	read -p "请输入要修改的root密码: " PASSWD
    sudo echo "root:$PASSWD" |chpasswd
	[ $? -eq 0 ] && color "密码修改成功!" 0 || color "密码修改失败!" 1
    sudo sed -ri.bak 's/^#(PermitRootLogin).*/\1 yes/p' /etc/ssh/sshd_config
	[ $? -eq 0 ] && color "已开启root远程登录!" 0 || color "开启失败!" 1
	sudo systemctl restart sshd 
}

yum_install () {
    yum -y install bash-completion psmisc lrzsz  tree man-pages redhat-lsb-core zip unzip bzip2 wget tcpdump ftp rsync vim lsof &> /dev/null
	[ $? -eq 0 ] && color "常用软件包安装成功!" 0 || color "常用软件包安装失败，请检查yum仓库!" 1
}

ubuntu_apt_install (){
    { apt update ; apt -y install bash-completion psmisc lrzsz  tree  zip unzip bzip2 wget tcpdump ftp rsync vim lsof ; } &> /dev/null
	[ $? -eq 0 ] && color "常用软件包安装成功!" 0 || color "常用软件包安装失败，请检查apt仓库!" 1
}

ntpdate_chrony () {
    yum -y install chrony &> /dev/null
	[ $? -eq 0 ] && color "chrony安装成功!" 0 || color "chrony安装失败，请检查yum仓库!" 1
    sed -ri.bak 's/^(server|pool.* iburst)/#\1/' /etc/chrony.conf

    cat >> /etc/chrony.conf <<-EOF
    server ntp.aliyun.com iburst
    server ntp1.aliyun.com iburst
    server ntp2.aliyun.com iburst
	EOF

    systemctl enable --now chronyd &> /dev/null
	[ $? -eq 0 ] && color "时钟同步完成!" 0 ||  color "时钟同步失败!" 1
}

ubuntu_ntpdate_chrony () {
    { apt update ; apt -y install chrony ; }  &> /dev/null
	[ $? -eq 0 ] && color "chrony安装成功!" 0 || color "chrony安装失败，请检查apt仓库!" 1
    sed -ri.bak 's/^(server|pool.* iburst)/#\1/' /etc/chrony/chrony.conf
    
	cat >> /etc/chrony/chrony.conf <<-EOF
    server ntp.aliyun.com iburst
    server ntp1.aliyun.com iburst
    server ntp2.aliyun.com iburst
	EOF
    
	systemctl enable --now chrony &> /dev/null
	[ $? -eq 0 ] && color "时钟同步完成!" 0 ||  color "时钟同步失败!" 1
}

senmail_mail () {
    while true;do
        while read -p "请输入邮箱账号: " MAILNAME; do
            if [[ $MAILNAME =~ .*@.*\.com ]]; then
                break
            else
                echo "输入错误，请输入正确的账号"
            fi
        done
            while read -p "请输入邮箱授权码: " PASSWORD; do
                    if [[ $PASSWORD =~ [[:alpha:]] ]]; then
                            break
                    else
                            echo "输入错误，请输入授权码"
                    fi
            done

        break
    done
}

mail_cat (){
    yum -y install postfix mailx sendmail &> /dev/null
	[ $? -eq 0 ] && color "邮件服务相关包安装成功!" 0 || color "邮件服务相关包安装失败，请检查yum仓库!" 1
    systemctl enable --now postfix sendmail &> /dev/null

    senmail_mail

	cat >> /etc/mail.rc <<-EOF
    set from=$MAILNAME
    set smtp=smtp.`echo $MAILNAME| awk -F@ '{print $2}'`
    set smtp-auth-user=$MAILNAME
    set smtp-auth-password=$PASSWORD
	EOF
	
	[ $? -eq 0 ] && color "邮件发送功能已配置完成!" 0 || color "邮件发送功能已配置失败!" 1
}

network_eth () {
    while true; do
        while read -p "请输入设备名: " NAME; do
            if [[ "$NAME" =~ eth[0-9]+ ]];then
                echo $NAME
                break
            else
                echo "输入错误，请重新输入设备名"
             fi
        done

        while read -p "请输入要配置的ip: " IP; do
            if [[ "$IP" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]];then
                echo $IP
                break
            else
                echo "输入错误，请重新输入ip"
            fi
        done

        while read -p "请输入网络id位数: " PREFIX; do
            if [ "$PREFIX" -ge 1 -a  "$PREFIX" -lt 32 ];then
                echo $PREFIX
                break
            else
                echo "输入错误，请重新输入网络id位数"
            fi
        done

        while read -p "请输入网关: " GATEWAY ;do
            if [[ "$GATEWAY" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]];then
                echo $GATEWAY
                break
            else
                echo "输入错误，请重新输入网关"
            fi
        done

        while read -p "请输入dns: " DNS ;do
            if [[ "$DNS" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]];then
                echo $DNS
                break
            else
                echo "输入错误，请重新输入网关"
            fi
        done
        break
    done
}

mod_network () {
    sed -ri.bak 's/(GRUB_CMDLINE_LINUX=.*)"/\1 net.ifnames=0"/' /etc/default/grub
    grub2-mkconfig -o /boot/grub2/grub.cfg &> /dev/null
	[ $? -eq 0 ] && color "网卡名已修改为ethX!" 0 || color "网卡名修改失败" 1
	color "重启生效!" 2

    network_eth

	cat >> /etc/sysconfig/network-scripts/ifcfg-$NAME <<-EOF
    DEVICE=$NAME
    NAME=$NAME
    BOOTPROTO=none
    IPADDR=$IP
    PREFIX=$PREFIX
    GATEWAY=$GATEWAY
    DNS1=$DNS
	EOF

	[ $? -eq 0 ] && color "IP配置完成!" 0 || color "IP配置失败" 1
}

ubuntu_mod_network () {
    sed -ri.bak 's/^(GRUB_CMDLINE_LINUX=).*/\1"net.ifnames=0"/' /etc/default/grub
    grub-mkconfig -o /boot/grub/grub.cfg &> /dev/null
	[ $? -eq 0 ] && color "网卡名已修改为$NAME!" 0 || color "网卡名修改失败" 1
	color "重启生效!" 2 

    network_eth

	cat > /etc/netplan/01-config.yaml <<-EOF
    network:
      version: 2
      renderer: networkd
      ethernets:
        $NAME:
          addresses:
          - $IP/$PREFIX
          gateway4: $GATEWAY
          nameservers:
            search:
            - yangedu.com
            addresses:
            - $DNS
	EOF

	[ $? -eq 0 ] && color "IP配置完成!" 0 || color "IP配置失败" 1
}

vimrc_read () {
    read -p "请输入作者姓名: " AUTHOR
    read -p "请输入联系方式(邮箱): " MAILS
    read -p "请输入网站: " YOUNAME
}

vimrc_cat () {
    if [[ $ID =~ rhel|centos|rocky ]];then
        rpm -q vim &> /dev/null ||  yum -y install vim &> /dev/null
        [ $? -eq 0 ] && color "vim,已安装" 0 || color "vim安装失败,请检查yum仓库" 1
    elif [ $ID = 'ubuntu' ];then
        dpkg -l vim &>/dev/null || { apt update; apt -y install vim ; }
        [ $? -eq 0 ] && color "vim,已安装" 0 || color "vim安装失败,请检查apt仓库" 1
    fi

    vimrc_read

    cat > ~/.vimrc <<-EOF
    set ignorecase
    set autoindent
    set ts=4
    set paste
    autocmd BufNewFile *.sh exec "call SetTitle()"
    func SetTitle()
        if expand("%:e") == 'sh'
            call setline(1,"#!/bin/bash")
            call setline(2,"#**********************************************************")
            call setline(3,"#Author:                    $AUTHOR")
            call setline(4,"#QQ:                        $MAILS")
            call setline(5,"#Date:                      ".strftime("%Y-%m-%d"))
            call setline(6,"#FileName:                  ".expand("%"))
            call setline(7,"#URL:                       $YOUNAME")
            call setline(8,"#Description:                   The test script")
            call setline(9,"#**********************************************************")
            call setline(10,"")
            endif
        endfunc
        autocmd BufNewFile * normal G
	EOF

    [ $? -eq 0 ] && color "~/vimrc配置完成" 0 ||  color "~/vimrc配置失败" 0
}

tencent () {
        URL=https://mirrors.tencent.com
}

nanjing () {
        URL=http://mirrors.nju.edu.cn
}

repo_bak () {
    mkdir -p /etc/yum.repos.d/bak`date +%F_%T`
    mv /etc/yum.repos.d/*.repo /etc/yum.repos.d/bak`date +%F_%T`
    [ $? -eq 0 ] && color "repo文件备份至/etc/yum.repos.d/bak`date +%F_%T`!" 0 ||color "repo文件备份失败!" 1
}

yum_base () {
    cat > /etc/yum.repos.d/base.repo <<-EOF
	[BaseOS]
	name=BaseOS
	baseurl=$URL/$ID/\$releasever/BaseOS/\$basearch/os
	gpgcheck=0
	
	[AppStream]
	name=AppStream
	baseurl=$URL/$ID/\$releasever/AppStream/\$basearch/os/
	gpgcheck=0
	
	[extras]
	name=extras
	baseurl=$URL/$ID/\$releasever/extras/\$basearch/os/
	gpgcheck=0
	
	[epel]
	name=epel
	baseurl=$URL/epel/\$releasever/Everything/\$basearch/
	gpgcheck=0
	EOF
}

tencent_base_repo () {
	repo_bak
    tencent
    yum_base
    echo $URL
    [ $? -eq 0 ] && color "腾讯源yum仓库配置成功!" 0 ||color "腾讯源yum仓库配置失败!" 1
}

nanjing_base_repo () {
	repo_bak
    nanjing
    yum_base
    echo $URL
    [ $? -eq 0 ] && color "南京大学源yum仓库配置成功!" 0 ||color "南京大学源yum仓库配置失败!" 1
}

list_bak () {
	cp -a /etc/apt/sources.list /etc/apt/sources.list.bak
    [ $? -eq 0 ] && color "sources.list备份成功!" 0 ||color "sources.list备份失败!" 1
}

ubuntu_apt () {

    cat > /etc/apt/sources.list <<-EOF
    deb $URL/$ID/ $VERSION_CODENAME main restricted universe multiverse
    deb-src $URL/$ID/ $VERSION_CODENAME main restricted universe multiverse
    deb $URL/$ID/ $VERSION_CODENAME-security main restricted universe multiverse
    deb-src $URL/$ID/ $VERSION_CODENAME-security main restricted universe multiverse

    deb $URL/$ID/ $VERSION_CODENAME-updates main restricted universe multiverse
    deb-src $URL/$ID/ $VERSION_CODENAME-updates main restricted universe multiverse
    
    deb $URL/$ID/ $VERSION_CODENAME-backports main restricted universe multiverse
    deb-src $URL/$ID/ $VERSION_CODENAME-backports main restricted universe multiverse
	EOF
}

ubuntu_tencent_sources_list () {
	list_bak
    tencent
    ubuntu_apt
	echo $URL
    [ $? -eq 0 ] && color "腾讯源apt仓库配置成功!" 0 ||color "腾讯源apt仓库配置失败!" 1
}   

ubuntu_nanjing_sources_list () {
	list_bak
    nanjing
    ubuntu_apt 
	echo $$URL
    [ $? -eq 0 ] && color "南京大学源apt仓库配置成功!" 0 ||color "南京大学源apt仓库配置失败!" 1
}



if_version () {
    if [[ $ID =~ rhel|centos|rocky ]];then
        echo $ID
        PS3="请选择需要执行的操作(1-12): "
        select HTTP in 关闭防火墙 关闭SElinux 自动挂载 常用软件安装 时钟同步 邮件服务 配置网卡和IP 腾讯源仓库 南京源仓库 vimrc文件编写 重启 退出; do
        	case $REPLY in
        	1)
        	    firewall_disable
        	    ;;
        	2)
        	    selinux_disabled
        	    ;;
        	3)
        	    iso_mount
        	    ;;
        	4)
        	    yum_install
				;;
        	5)
        	    ntpdate_chrony
        	    ;;
        	6)
        	    mail_cat
        	    ;;
        	7)
        	    mod_network
        	    ;;
        	8)
		    	tencent_base_repo
				;;
			9)
				nanjing__base_repo
				;;
        	10)
        	    vimrc_cat
        	    ;;
        	11)
				reboot
				;;
			12)
        	    color "$ID 已完成您选择的操作,部分操作需要重启生效,再见!" 2
        	    break
        	    ;;
        	*)
        	    color "输入错误，请重新选择" 1
        	esac
        done

    elif [ $ID = 'ubuntu' ];then
        echo $ID
        PS3="请选择需要执行的操作(1-12）: "
        select HTTP in 关闭防火墙 自动挂载 修改时区 开启root登录 安装常用软件 时钟同步 配置网卡名和IP 腾讯源仓库 南京源仓库 vimrc文件编写 重启 退出; do
        	case $REPLY in
        	1)
        	    ubuntu_firewall_mask
        	    ;;
        	2)
        	    ubuntu_iso_mount
        	    ;;
        	3)
        	    ubuntu_timedate
        	    ;;
        	4)
        	    ubuntu_root_ssh
        	    ;;
        	5)
        	    ubuntu_apt_install
        	    ;;
        	6)
        	    ubuntu_ntpdate_chrony
        	    ;;
        	7)
        	    ubuntu_mod_network
        	    ;;
        	8)
        	    ubuntu_tencent_sources_list
        	    ;;
        	9)
				ubuntu_nanjing_sources_list
				;;
			10)
        	    vimrc_cat
        	    ;;
			11)
				reboot
				;;
        	12)
        	    color "$ID 已完成您选择的操作,部分操作需要重启生效,再见!" 2
        	    break
        	    ;;
        	*)
        	    cplpr "选择错误，请重新选择" 1
        	esac
        done

    else
        color "不支持此操作系统，退出!" 1
        exit
    fi
}

if_version

