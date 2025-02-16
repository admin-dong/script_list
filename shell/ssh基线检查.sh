#!/bin/bash
backup_ssh_config(){
    backup_time=$(date +%Y%m%d%H%M)
    cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak_${backup_time}
}
 
remove_ssh_config(){
    local config_option=$1
    sed -i "s@^\s*${config_option}\s*.*@#&@" /etc/ssh/sshd_config
}
 
update_ssh_config(){
    local config_option=$1
    local config_value=$2
    sed -i "s@^\s*${config_option}\s*.*@#&@" /etc/ssh/sshd_config
    echo "${config_option} ${config_value}" >> /etc/ssh/sshd_config
}
 
fix_ssh(){
 
    # 确保SSH中HostbasedAuthentication关闭
    update_ssh_config "HostbasedAuthentication" "no"
 
    # 确保SSH PermitEmptyPasswords被禁用
    update_ssh_config "PermitEmptyPasswords" "no"
 
    # 使用更加安全的Ciphers算法
    update_ssh_config "Ciphers" "aes256-ctr,aes192-ctr,aes128-ctr"
 
    # 确保使用更安全的MAC算法
    update_ssh_config "MACs" "hmac-sha2-512,hmac-sha2-256"
 
    # 需限制SSH服务使用的密钥文件权限
    chmod 400 /etc/ssh/*key /etc/ssh/*key.pub
    chown -R root:root /etc/ssh
 
    # 确保SSH X11转发被禁用
    update_ssh_config "X11Forwarding" "no"
 
    # 确保SSH中MaxAuthTries设置小于等于4
    update_ssh_config "MaxAuthTries" "4"
 
    # 确保SSH中IgnoreRhosts设置为enabled
    update_ssh_config "IgnoreRhosts" "yes"
 
    # 确保SSH PermitUserEnvironment被禁用
    update_ssh_config "PermitUserEnvironment" "no"
 
    # 确保配置了SSH空闲超时间隔	
    update_ssh_config ClientAliveInterval 300
    update_ssh_config ClientAliveCountMax 0
 
    # 确保设置了SSH警告提示信息
    update_ssh_config Banner /etc/issue.net
 
    # 确保SSH LoginGraceTime设置为一分钟或更短
    update_ssh_config LoginGraceTime 60
 
    # 关闭SFTP服务
    remove_ssh_config "Subsystem"
}
 
 
 
backup_ssh_config
fix_ssh