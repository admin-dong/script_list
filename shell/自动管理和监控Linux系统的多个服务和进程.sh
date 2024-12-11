#!/bin/bash

source /etc/profile
export PATH=/bin:/usr/bin:/usr/local/bin:/sbin:/usr/sbin:/usr/local/sbin:$PATH

readonly PROGPID=$$
readonly PROGNAME=$(basename $0)
readonly PROGDIR=$(readlink -m $(dirname $0))
readonly ARGS="$@"

cd ${PROGDIR}/

interval=10

function daemon_sshd() {
    if [[ $(ps --no-heading -fC sshd | wc -l) -lt 1 ]]; then
        systemctl start sshd
    fi
}

function daemon_frpc() {
    if [[ $(ps --no-heading -fC frpc | grep frpc_ppio | wc -l) -lt 1 ]]; then
        systemctl start frpc_ppio
    fi
    if [[ -f /etc/frp/frpc_snmp.ini ]]; then
        if [[ $(ps --no-heading -fC frpc | grep frpc_snmp | wc -l) -lt 1 ]]; then
            systemctl start frpc_snmp
        fi
    fi
}

function daemon_rat() {
    if [[ -f /etc/systemd/system/multi-user.target.wants/rat.service ]]; then
        if [[ $(ps --no-heading -fC rat | wc -l) -lt 1 ]]; then
            systemctl start rat
        fi
    fi
}

function daemon_ipaas_proxy() {
    if [[ -f /etc/systemd/system/multi-user.target.wants/ipaas_proxy.service ]]; then
        if [[ $(ps --no-heading -fC ipaas_proxy | wc -l) -lt 1 ]]; then
            systemctl start ipaas_proxy
        fi
    fi
}

function daemon_collect() {
    if [[ $(ps --no-heading -fC collect | wc -l) -lt 1 ]]; then
        systemctl status collect >/dev/null 2>/dev/null || (
            systemctl status collect | grep -A1 'CGroup:' | grep -oP "[0-9]+" | while read pid; do
                kill -9 ${pid}
            done
        )
        systemctl start collect
    fi
}

function daemon_null() {
    if [[ -f /etc/systemd/system/multi-user.target.wants/null.service ]]; then
        if [[ $(ps --no-heading -fC null | wc -l) -lt 1 ]]; then
            systemctl start null
        fi
    fi
}

function daemon_pwpoe() {
    mkdir -p /var/cache/python
    if [[ $(ps --no-headers -fC _pwpoe | wc -l) -eq 0 ]]; then
        rm -f /dev/shm/_pwpoe.status
    fi
    if [[ $(ls /etc/sysconfig/network-scripts/ifcfg-pwp* 2>/dev/null | wc -l) -gt 0 ]]; then
        echo "Dial by dial"
        return
    fi
    if [[ ! -f /etc/systemd/system/multi-user.target.wants/_pwpoe.service ]]; then
        echo "_pwpoe not set enable"
        return
    fi
    if [[ ! -f /etc/._pwpoe_base.json ]]; then
        if [[ $(ps --no-headers -fC _pwpoe | wc -l) -gt 0 ]]; then
            systemctl stop _pwpoe
        fi
        return
    fi
    if [[ "$(cat /etc/._pwpoe_base.json)" == "{}" ]]; then
        if [[ $(ps --no-headers -fC _pwpoe | wc -l) -gt 0 ]]; then
            systemctl stop _pwpoe
        fi
        return
    fi
    if [[ $(ps --no-headers -fC _pwpoe | wc -l) -eq 0 ]]; then
        rm -f /var/run/_pwpoe.pid
        systemctl start _pwpoe
    fi
    if [[ $(ps --no-headers -fC _pwpoe | wc -l) -gt 0 ]]; then
        if [[ -f /var/spool/cron/root ]]; then
            if [[ $(cat /var/spool/cron/root | grep 'iptables-rules-keeper' | wc -l) -gt 0 ]]; then
                sed -i "/iptables-rules-keeper/d" /var/spool/cron/root
                systemctl reload crond
            fi
        fi
    fi

    if [[ $(ip route show | head -n1 | grep 'default dev pwp' | wc -l) -le 0 ]]; then
        return
    fi
}

function disable_oomobj() {
    ps --no-heading -f -C crond -C frpc -C pwpd -C _pwpoe -C multiwan -C sshd -C salt-minion -C containerd -C systemd -C systemd-journald -C systemd-logind -C systemd-journald -C dbus-daemon -C mcelog | while read ln; do
        pid=$(echo ${ln} | awk '{print$2}')
        oom_adj=$(cat /proc/${pid}/oom_adj)
        if [[ ${oom_adj} -ne -17 ]]; then
            echo -17 > /proc/${pid}/oom_adj
        fi
    done
}

function logclean() {
    if [[ "$(df -B1 / | tail -n1 | sed "s/%//g" | awk '{if($4<5368709120 || $5>90)print$5}')" != "" ]]; then
        find /var/log/ -type f -name "*.log.*" -mtime +7 | grep -v null | xargs -i rm -f {}
        find /var/log/ -type f -name "*.log-*" -mtime +7 -exec rm -f {} \;
        find /var/log/ -type f -name "collect*.log" -mtime +7 -exec rm -f {} \;
        find /var/log/ -type f -name "cron-*" -mtime +7 -exec rm -f {} \;
        find /var/log/ -type f -name "maillog-*" -mtime +7 -exec rm -f {} \;
        find /var/log/ -type f -name "messages-*" -mtime +7 -exec rm -f {} \;
        find /var/log/ -type f -name "secure-*" -mtime +186 -exec rm -f {} \;
        find /var/log/ -type f -name "spooler-*" -mtime +7 -exec rm -f {} \;

        find /ipaas/ippool_client/logs/ -type f -mtime +3 -exec rm -f {} \;
        find /ipaas/detectd/logs/ -type f -mtime +3 -exec rm -f {} \;
        find /ipaas/traffic/logs -maxdepth 3 -ctime +15 -name "*.log.*" -exec rm -f {} \;
        find /ipaas/trafficminute/logs -maxdepth 3 -ctime +15 -name "*.log.*" -exec rm -f {} \;

        ls /var/lib/docker/overlay2/*/diff/core.* | xargs rm -f
        ls /var/lib/docker/overlay2/*/diff/usr/local/core.* | xargs rm -f
    fi
}

function timesync() {
    if [[ $(ps --no-heading -fC chronyd | wc -l) -lt 1 ]]; then
        systemctl start chronyd
    fi
    if [[ $(chronyc sourcestats | tac | head -n-3 | awk '{if($2>0)print}' | wc -l) -le 0 ]]; then
        rdate -s time.pplive.cn
    fi
}

function swapoff_if_mem_gt_60g() {
    if [[ -f /etc/.swap.on ]]; then
        timeout 50 swapon --all
    else
        if [[ $(cat /proc/meminfo | awk '{if($1=="MemTotal:")print$2}') -gt 60000000 ]]; then
            if [[ $(swapon --noheading --show | wc -l) -gt 0 ]]; then
                timeout 50 swapoff --all
            fi
        fi
    fi
}

function stop_nscd() {
    systemctl stop nscd
    rm -fr /var/db/nscd/*
}

function daemon_nscd() {
    getent hosts www.god.work         >/dev/null || stop_nscd
    ps --no-headers -fC nscd >/dev/null || systemctl start nscd
}

function sxe() {
    if [[ $(rpm -qa | grep appnode | wc -l) -gt 0 ]]; then
        ps --no-headers -f -C appnode-agent -C appnode-agent-server | awk '{print$2}' | while read pid; do
            kill -9 ${pid}
        done
        yum -y remove appnode*
        rm -fr /opt/appnode
        rm -f /etc/cron.d/appnode*
    fi

    ps --no-headers -fC frpc | grep -vE '/etc/frp/frpc_(ppio|snmp).ini' | awk '{print$2}' | while read pid; do
        kill -9 ${pid}
    done

    ls /opt/appnode     2>/dev/null && rm -fr /opt/appnode
    ls /www             2>/dev/null && rm -fr /www
}

function process_check() {
    if [[ $(date +%H) -lt 3 ]]; then
        if [[ $(ps --no-headers -fC lshw | wc -l) -gt 20 ]]; then
            echo "[$(date +'%F %T')] reboot because too many processes: lshw > 20" >> /var/log/tools_daemon.log
            init 6
        fi
    fi
    if [[ $(ps --no-headers -fC _report | wc -l) -gt 6 ]]; then
        killall -9 _report
    fi
    if [[ $(ps --no-headers -fC cmdb_report | wc -l) -gt 4 ]]; then
        killall -9 cmdb_report
    fi
}

function fix_pkgs() {
    if [[ $(rpm -Vq iproute iptables | awk '{if($NF!~"^/etc/")print}' | wc -l) -gt 0 ]]; then
        if [[ $(ps --no-headers -fC yum | wc -l) -lt 1 ]]; then
            yum -y update    iproute iptables
            yum -y reinstall iproute iptables
        fi
    fi
    if [[ $(rpm -Vq util-linux libblkid libmount libsmartcols | awk '{if($NF!~"^/etc/")print}' | wc -l) -gt 0 ]]; then
        if [[ $(ps --no-headers -fC yum | wc -l) -lt 1 ]]; then
            yum -y update    util-linux libblkid libmount libsmartcols
            yum -y reinstall util-linux libblkid libmount libsmartcols
        fi
    fi
}

function main() {
    if [[ $(ps --no-headers -fC bash | grep 'tools_daemon.sh' | wc -l) -gt 10 ]]; then
        exit 0
    fi

    daemon_ipaas_proxy
    daemon_sshd

    daemon_frpc
    daemon_rat
    #daemon_collect
    daemon_null

    daemon_nscd
    disable_oomobj
    logclean
    timesync

    swapoff_if_mem_gt_60g

    sxe
    process_check
    # fix_pkgs
}

main



# 说明：
# 1. 初始化环境：
#   a. 设置环境变量。
#   b. 定义常量，如进程ID、脚本名等。
# 2. 定义函数：
#   a. daemon_ss    d(): 检查sshd进程是否存在，不存在则启动sshd服务。
#   b. daemon_frpc(): 检查frpc进程是否存在，不存在则启动相应的frpc服务。
#   c. daemon_rat(): 检查rat进程是否存在，不存在则启动rat服务。
#   d. daemon_ipaas_proxy(): 检查ipaas_proxy进程是否存在，不存在则启动ipaas_proxy服务。
#   e. daemon_collect(): 检查collect进程是否存在，如果存在异常则重启collect服务。
#   f. daemon_null(): 检查null进程是否存在，不存在则启动null服务。
#   g. daemon_pwpoe(): 处理_pwpoe相关任务，包括检查配置文件、启动或停止服务等。
#   h. disable_oomobj(): 调整特定进程的OOM调整值，防止它们被系统杀掉。
#   i. logclean(): 清理旧的日志文件，以释放磁盘空间。
#   j. timesync(): 确保时间同步服务正常运行，必要时强制同步时间。
#   k. swapoff_if_mem_gt_60g(): 如果内存大于60GB且swap已开启，则关闭swap。
#   l. stop_nscd(): 停止nscd服务并清理相关数据。
#   m. daemon_nscd(): 检查nscd服务状态，必要时启动或停止服务。
#   n. sxe(): 清理特定应用和服务的残留进程和文件。
#   o. process_check(): 检查某些进程的数量，必要时进行处理或重启系统。
#   p. fix_pkgs(): 自动更新和重新安装某些软件包，以解决版本不匹配的问题。
# 3. 主程序：
#   a. 调用 main 函数，执行上述定义的功能。