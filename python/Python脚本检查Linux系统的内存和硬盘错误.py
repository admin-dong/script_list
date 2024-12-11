#!/usr/bin/env python3
# coding: utf-8
import sys
sys.path.append('/usr/lib/python3.6/paiutils')  # 添加自定义库的路径
from utils import run_command  # 导入run_command函数，用于执行shell命令
from datetime import datetime  # 导入datetime模块，用于获取当前时间

# 检查内存错误
def check_mem_error():
    # 构造命令来查找EDAC监控子系统中的内存错误计数
    cmd = "grep '[0-9]' /sys/devices/system/edac/mc/mc*/csrow*/ch*_ce_count 2>/dev/null"
    status, result = run_command(cmd, branch=True)  # 执行命令并获取结果

    # 如果命令执行成功
    if status == 0:
        for r in result:
            # 分割输出结果
            words = r.split(':')
            # 如果错误计数大于0
            if int(words[1]) > 0:
                print(words[1])  # 输出错误计数
            print(r)  # 输出完整行

    # 返回一个字典，包含内存错误信息
    return {"mem_hd_err": result}

# 检查硬盘错误
def check_disk_error():
    disk_error = dict()  # 创建一个空字典来存储硬盘错误信息
    # 获取当前时间字符串，格式为：月 日 时
    time_string = datetime.now().strftime("%b %e %H")

    # 构造命令来查找/var/log/messages中的硬盘错误记录
    cmd = f'''
    cat /var/log/messages |
    grep -iP "^{time_string}.+ kernel: (blk_update_request: (I/O error|critical medium error)|Buffer I/O error|ata.+: error|sd.+(Medium Error|read error)|.+(xfs_error_report|xfs_corruption_error)|XFS.+error)" |
    grep -v 'dev fd0'
    '''
    try:
        status, result = run_command(cmd, branch=True)  # 执行命令并获取结果
    except Exception as e:
        status = 1  # 如果发生异常，设status为1

    # 如果命令执行成功
    if status == 0:
        for r in result:
            # 分割输出结果
            words = r.split(',')
            # 如果输出中有'dev'关键字
            if len(words) > 1 and 'dev' in words[1]:
                dev = words[1].split()  # 再次分割以获取设备名
                key = dev[1]  # 获取设备名
                if key not in disk_error:  # 如果设备名不在字典中
                    disk_error[key] = 1  # 将设备名添加到字典中

    # 返回一个字典，包含硬盘错误信息
    return disk_error

# 主程序入口
if __name__ == "__main__":
    # 检查命令行参数数量
    if len(sys.argv) != 2:
        sys.exit(-1)  # 如果参数数量不正确，退出程序

    # 如果第一个命令行参数是"disk_error"
    if sys.argv[1] == "disk_error":
        print(check_disk_error())  # 输出硬盘错误检查的结果