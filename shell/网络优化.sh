#!/bin/bash


source /etc/profile

#if [[ $(date +%H) -gt 17 ]]; then
#    exit
#fi

#if [[ -f /dev/shm/set_netdev_affinity.timestamp ]]; then
#    if [[ $(date +%s) -lt $(( $(cat /dev/shm/set_netdev_affinity.timestamp) + 86400 )) ]]; then
#        exit
#    fi
#fi

systemctl stop irqbalance
# systemctl disable irqbalance

#sysctl -w net.core.netdev_budget=600
echo 32768 > /proc/sys/net/core/rps_sock_flow_entries

cpu_cores_num=$(cat /proc/cpuinfo | grep ^processor | wc -l)

function calc_affinity() {
    cpu_core_index=$1
    affinity=0
    for((i=0; i<=${cpu_core_index}; i++)); do
        ((affinity|=1<<i))
    done
    result=$(printf '%x\n' "${affinity}")
    length=${#result}
    if [[ ${length} -gt 16 ]]; then
        result=$(sed 's/.\{16\}$/,&/' <<< "$result")
    fi
    if [[ ${length} -gt 8 ]]; then
        result=$(sed 's/.\{8\}$/,&/' <<< "$result")
    fi
    echo ${result}
}

function set_affinity() {
    ifname=$1
    netdev_driver=$2
    let i=0

    grep_regexp="${ifname}-(Tx|Rx|tx|rx)"
    if [[ "${netdev_driver}" == "mlx4_en" ]]; then
        businfo=$(ethtool -i ${ifname} | awk -F': ' '{if($1=="bus-info")print$2}')
        grep_regexp="mlx4-[0-9]+@${businfo}"
    elif [[ "${netdev_driver}" == "bnx2x" ]]; then
        grep_regexp="${ifname}-fp"
    elif [[ $(grep -P "${grep_regexp}" /proc/interrupts|wc -l) -le 1 ]]; then
        return
    fi
    grep -P "${grep_regexp}" /proc/interrupts | awk -F':' '{print$1}' | while read irq_num; do
        affinity=$(calc_affinity ${i})
        echo "${ifname} ${irq_num} ${affinity}"
        echo ${affinity} > /proc/irq/${irq_num}/smp_affinity
        let i+=1
        if [[ $i -ge ${cpu_cores_num} ]]; then
            let i=0
        fi
    done
}

ls /sys/class/net | sort | uniq >/tmp/ifs
ls /sys/devices/virtual/net | sort | uniq >/tmp/vifs

sort -m <(cat /tmp/ifs) <(cat /tmp/vifs) <(cat /tmp/vifs) | uniq -u | while read ifname; do
    rq_count=$(ls /sys/class/net/${ifname}/queues/rx-* -d | wc -l)
    rps_flow_cnt_value=$(expr 32768 / $rq_count)

    ls /sys/class/net/${ifname}/queues/rx-* -d | while read fd; do
        echo $rps_flow_cnt_value > ${fd}/rps_flow_cnt
        echo $(cat ${fd}/rps_cpus | sed 's/0/f/g') >  ${fd}/rps_cpus
    done

    netdev_driver=$(ethtool -i ${ifname} | awk -F': ' '{if($1=="driver")print$2}')

    if [[ "${netdev_driver}" == "r8169" ]]; then
        continue
    fi

    # support ixgbe, bnx2x, tg3, mlx4_en, qlcnic

    if [[ "$(cat /sys/class/net/${ifname}/operstate)" == "up" ]]; then
        rx_ring=$(ethtool -g ${ifname} | grep '^RX:' | awk -F':' '{print$2}' | head -n1)
        if [[ ${rx_ring} -gt 0 ]]; then
            ethtool -G ${ifname} rx ${rx_ring}
        fi
        tx_ring=$(ethtool -g ${ifname} | grep '^TX:' | awk -F':' '{print$2}' | head -n1)
        if [[ ${tx_ring} -gt 0 ]]; then
            ethtool -G ${ifname} tx ${tx_ring}
        fi
        rx_channel=$(ethtool -l ${ifname} | grep '^RX:' | awk -F':' '{print$2}' | head -n1)
        if [[ ${rx_channel} -gt 0 ]]; then
            ethtool -L ${ifname} rx ${rx_channel}
        fi
        tx_channel=$(ethtool -l ${ifname} | grep '^TX:' | awk -F':' '{print$2}' | head -n1)
        if [[ ${tx_channel} -gt 0 ]]; then
            ethtool -L ${ifname} tx ${tx_channel}
        fi

        combined=$(ethtool -l ${ifname} | grep ^Combined | awk -F':' '{print$2}' | head -n1)
        if [[ ${combined} -gt 1 ]]; then
            if [[ ${combined} -gt ${cpu_cores_num} ]]; then
                combined=${cpu_cores_num}
            fi
            ethtool -L ${ifname} combined ${combined}
        fi

        set_affinity ${ifname} ${netdev_driver}
    fi
done


# #说明：
# 1. 初始化：
#   a. 加载 /etc/profile 中的环境变量设置。
# 2. 停止 irqbalance 服务：
#   a. systemctl stop irqbalance：停止 irqbalance 服务，该服务可以动态地调整中断亲和性。
# 3. 调整系统参数：
#   a. echo 32768 > /proc/sys/net/core/rps_sock_flow_entries：设置每个接收队列的最大 RPS 流条目数。
# 4. 计算 CPU 核心数量：
#   a. cpu_cores_num=$(cat /proc/cpuinfo | grep ^processor | wc -l)：获取系统中处理器的数量。
# 5. 定义函数：
#   a. calc_affinity(cpu_core_index): 计算指定 CPU 核心索引的中断亲和性值。
#   b. set_affinity(ifname, netdev_driver): 设置指定网络设备的中断亲和性。
# 6. 处理网络设备：
#   a. 获取所有物理和虚拟网络接口的名称。
#   b. 遍历每个网络接口，并进行如下操作：
#     ■ 设置 RPS 流条目的数量。
#     ■ 设置 RPS CPU 亲和性。
#     ■ 获取网络设备的驱动程序名称。
#     ■ 如果网络接口处于“up”状态，则：
#       ● 设置 RX 和 TX 环的大小。
#       ● 设置 RX 和 TX 队列的数量。
#       ● 设置组合队列的数量。
#       ● 设置中断亲和性。
# 注意事项：
# ● 确保系统上安装了必要的工具（如 ethtool）。
# ● 脚本需要有执行系统命令的权限。
# ● 考虑在执行重要操作之前增加更多的错误处理和日志记录，以便于调试和服务恢复。
# ● 修改系统设置可能会影响系统稳定性，请谨慎操作。
