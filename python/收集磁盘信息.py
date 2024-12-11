#!/usr/bin/env python3
# coding:utf-8

import os
import sys
import json
import time
import multiprocessing

from check_hard_error import check_disk_error
sys.path.append('/usr/lib/python3.6/paiutils')

from lshw import LSHW
from utils import run_command, get_block_device_without_root, get_disk_size

# 定义用于获取硬盘大小的ioctl命令
BLKGETSIZE64 = 0x80081272
# 定义SSD的IOPS阈值
SSD_IOPS = 10000

# 获取硬盘类型
def get_disk_type():
    disk_type = dict()
    status, output = run_command('/bin/bash /opt/scripts/list_disk.sh')
    if status == 0:
        for line in output:
            if line.startswith("/dev"):
                words = line.split()
                if len(words) == 2:
                    dev = words[0].split("/")[-1]
                    if "nvme" in dev.lower():
                        disk_type[dev] = "NVME"
                    elif int(words[1]) > SSD_IOPS:
                        disk_type[dev] = "SSD"
                    else:
                        disk_type[dev] = "HDD"
    return disk_type

# 获取硬盘分区的使用情况
def get_disk_partitions_usage(total, dev_path):
    dev_name = dev_path.split('/')[-1]
    total_used = 0
    total_size = 0
    dev_list = [f'/dev/{x}' for x in os.listdir(f'/sys/block/{dev_name}') if x.startswith(dev_name) and x != dev_name]

    for dev in dev_list:
        status, output = run_command(f'df -B 1 {dev}')

        if status == 0:
            try:
                device, total_s, used = output[1].split()[:3]
                if device == dev:
                    total_used += int(used)
                    total_size += int(total_s)
            except:
                pass
    if total_size == total:
        percent_used = round(total_used / total_size * 100, 2)
    elif total_used > 0:
        percent_used = round(total_used / int(total) * 100, 2)
    else:
        percent_used = 0
    return percent_used

# 获取硬盘信息
def get_disk_info(devpath):
    status, output = run_command(f'df -B 1 {devpath}')
    if status == 0:
        try:
            device, size_total, size_used, size_available, percent_used_str = output[1].split()[:5]
            if device == devpath:
                return int(size_total), float(percent_used_str.split('%')[0])
            else:
                total_size = get_disk_size(devpath)
                return total_size, get_disk_partitions_usage(total_size, devpath)
        except:
            pass
    return 0, 0

# 读取磁盘统计信息
def read_diskstats():
    diskstats = [x.split() for x in open('/proc/diskstats', mode='r').read().strip().split('\n')]
    result = dict(zip([x[2] for x in diskstats], [[int(y) for y in x[3:]] for x in diskstats]))
    return result

# 获取I/O数据
def get_iodata(pipe):
    diskioinfo = {}
    ioinfo = read_diskstats()
    time.sleep(3)
    ioinfo2 = read_diskstats()
    for k, v in ioinfo.items():
        diskioinfo[k] = [
            ioinfo2[k][0] - v[0], ioinfo2[k][3] - v[3],
            ioinfo2[k][4] - v[4], ioinfo2[k][7] - v[7],
            ioinfo2[k][9] - v[9]
        ]
    pipe.send(diskioinfo)

# 获取LVM使用情况
def get_lvm_usage():
    lvm_usage = {}
    status, output = run_command('pvs --noheadings --units B 2>/dev/null')
    if status == 0:
        for dev in output:
            dev = dev.split()
            size = int(dev[4].split('B')[0])
            free = int(dev[5].split('B')[0])
            lvm_usage[dev[0].split('/')[-1]] = round(float((size - free) / size) * 100, 1)
    return lvm_usage

# 主函数
def main():
    hw = LSHW()
    result = {}
    disk_type = get_disk_type()

    # 获取非root设备列表
    devpaths_without_root = get_block_device_without_root(removable=True)
    for storages_ctrl in hw.lshw_result['storages']:
        for disk in storages_ctrl['children']:
            devpath = mountpoint = None
            for logicalname in disk['logicalname']:
                if logicalname.startswith('/dev/'):
                    devpath = logicalname
                else:
                    mountpoint = logicalname
            if devpath:
                devname = os.path.basename(devpath)

                # 判断是否为系统盘
                if devname in devpaths_without_root:
                    isSystemDisk = False
                else:
                    isSystemDisk = True

                # 获取硬盘容量和使用率
                diskcap, diskusage = get_disk_info(devpath)
                disktype = f"{disk['transport_protocol']}_{disk_type.get(devname, 'HDD')}"

                # 更新结果字典
                result[devname] = {
                    'diskcap': diskcap,
                    'disktype': disktype,
                    'diskusage': diskusage,
                    'mountpoint': mountpoint,
                    'IsSystemDisk': isSystemDisk
                }

    # 多进程获取I/O数据
    multijobs = []
    recvs = []
    recv, send = multiprocessing.Pipe(False)
    data = multiprocessing.Process(target=get_iodata, args=(send,))
    multijobs.append(data)
    recvs.append(recv)
    data.start()

    for proc in multijobs:
        proc.join()

    # 获取LVM使用情况
    lvm_usage = get_lvm_usage()
    disk_hd_error = check_disk_error()

    # 收集I/O数据
    iodata = [r.recv() for r in recvs]
    for r in iodata:
        for k, v in r.items():
            if k in result.keys():
                # 计算I/O延迟
                result[k].update({
                    'rddelay': 0 if v[0] == 0 else float(v[1] / float(v[0])),
                    'wrdelay': 0 if v[2] == 0 else float(v[3] / float(v[2])),
                    'ioduration': v[4] / 3000.0,
                    'hderror': 0
                })
                # 更新LVM使用率
                if result[k]["diskusage"] == 0 and k in lvm_usage.keys():
                    result[k].update({"diskusage": lvm_usage[k]})
                # 更新硬盘错误信息
                if disk_hd_error.get(k):
                    result[k].update({"hderror": 1})

    # 打印结果
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()