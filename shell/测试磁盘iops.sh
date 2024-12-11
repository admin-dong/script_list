#!/bin/bash

function internal_disk_sector() {
    local DISK=$(basename $1)
    cat "/sys/block/$DISK/size"
}

function internal_disk_size() {
    local DISK=$(basename $1)
    internal_disk_sector "$DISK" | xargs -i echo "({} / 2048 - 2)" | bc
}

function list_disk() {
    local PHY_DISKS=($(lsblk -pndo NAME,TYPE,TRAN | awk '$2=="disk" && $3!="usb" {print $1}'))
    DISKS=($(for D in "${PHY_DISKS[@]}"; do echo "$D"; done | sort -u -V))
    echo "DISKS:" "${DISKS[@]}" >&2
    for D in "${DISKS[@]}"; do
        if [ "$(lsblk -ro NAME,MOUNTPOINT $D | awk '{if(NR>1&&($2=="/"||substr($2,1,5)=="/boot"||substr($2,1,6)=="[SWAP]"))print $1,$2}' | wc -l)" -eq 0 ]; then
            local DISK_SIZE=$(internal_disk_size "$D")
            if [ "$DISK_SIZE" -gt 0 ]; then
                echo "$D"
            fi
        fi
    done
}

function clear_old_logs() {
    local LOGS=$(ls /var/log/*_iops_*_read_*.log 2>/dev/null)
    local DAYS=7
    while [ $DAYS -ge 0 ]; do
        LOGS=$(echo "$LOGS" | grep -v $(date -d "-$DAYS days" "+%Y-%m-%d"))
        DAYS=$(($DAYS - 1))
    done
    rm -f $LOGS
}

function disk_iops_read() {
    local DISK=$1
    local SIZE=$2
    if [ -z "$SIZE" ]; then
        SIZE=4
    fi
    local TIME=$3
    if [ -z "$TIME" ]; then
        TIME=4
    fi
    clear_old_logs
    local NAME=$(date +%Y-%m-%d)_iops_${SIZE}k_read_$(echo "$DISK" | sed 's|/dev/||')
    if [ ! -f /var/log/$NAME.log ]; then
        NEED_TEST=1
    else
        # if history exists, check whether mtime is before boot
        local HISORY_MTIME
        local UPTIME

        HISORY_MTIME=$(stat -c '%Y' /var/log/$NAME.log)
        if [ $? -gt 0 ] || [ -z "$HISORY_MTIME" ]; then
            return 1
        fi

        UPTIME=$(grep btime /proc/stat | awk '{print $2}')

        if [ "$UPTIME" -gt "$HISORY_MTIME" ]; then
            NEED_TEST=1
        fi
    fi

    if [ -n "$NEED_TEST" ]; then
        if ! fio -output=/var/log/$NAME.log \
            -name=$NAME \
            -filename=$DISK \
            -ioengine=libaio \
            -direct=1 \
            -bs=${SIZE}k \
            -rw=randread \
            -iodepth 32 \
            -thread \
            -runtime=$TIME &>/dev/null; then
            return 1
        fi
    fi

    local IOPS=$(cat /var/log/$NAME.log | grep IOPS= | awk -F '[=,]' '{print $2}')
    if [ $(echo "$IOPS" | grep -i "k$" | wc -l) -gt 0 ]; then
        IOPS=$(echo "$IOPS" | sed 's/[kK]//' | awk '{print 1000*$1}')
    fi

    if [ -z "$IOPS" ]; then
        return 1
    fi

    echo $IOPS
}

function main() {
    for DISK in $(list_disk); do
        if ! IOPS=$(disk_iops_read $DISK); then
            echo "failed to get iops on disk $DISK" >&2
            echo "$DISK" "0"
            continue
        fi
        echo "$DISK" "$IOPS"
    done
}

main


#这段Bash脚本用于列出系统中的物理磁盘，并针对每个磁盘执行随机读取I/O性能测试（IOPS），然后输出磁盘名及其对应的IOPS值。
#需要  lsblk, fio
# #1. 定义函数：
#   a. internal_disk_sector(DISK): 获取指定磁盘的总扇区数。
#   b. internal_disk_size(DISK): 根据磁盘的总扇区数计算磁盘大小（单位：GB）。
#   c. list_disk(): 列出系统中的物理磁盘，排除那些作为其他磁盘或逻辑卷后端的磁盘。
#   d. clear_old_logs(): 清除七天前的日志文件。
#   e. disk_iops_read(DISK, [SIZE], [TIME]): 执行随机读取I/O性能测试（IOPS），并返回测试结果。
#   f. main(): 主函数，遍历每个磁盘并调用 disk_iops_read 函数。
# 2. 主程序：
#   a. 调用 main 函数，遍历每个磁盘并获取其IOPS值。