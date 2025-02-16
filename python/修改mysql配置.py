
# -*- coding: UTF-8 -*-
'''


'''

import json
from optparse import OptionParser
import warnings
import sys
import os
import shutil
import datetime
warnings.filterwarnings("ignore")

default_mysql_parameter = {
            'innodb_flush_log_at_trx_commit' : None,
            'sync_binlog' : None,
            'innodb_buffer_pool_size' : None,
            'max_connections' : None,
            'long_query_time' : None,
            'sql_mode' : None,
            'expire_logs_days' : None,
            'binlog_expire_logs_seconds' : None,
            'innodb_io_capacity' : None,
            'interactive_timeout' : None,
            'wait_timeout' : None,
            'innodb_read_io_threads' : None,
            'innodb_write_io_threads' : None,
            'innodb_thread_concurrency' : None,
            'slave_parallel_workers' : None,
            'default_authentication_plugin' : None,
            'innodb_purge_threads' : None,
            'innodb_page_cleaners' : None,
            'innodb_lock_wait_timeout' : None,
            'max_allowed_packet' : None,
            'innodb_open_files' : None,
            'table_definition_cache' : None,
            'table_open_cache' : None,
            'open_files_limit' : None
        }
# 返回值 说明
#  1 成功
#  0 未执行
# -10 参数key不合法
# -20 参数值为空
# -30 配置文件不存在
# -40 系统级问题：权限、磁盘、IO等
# -50 暂不支持该操作系统
# 操作文件前备份该文件，文件名拼接时间戳
def upd_mysql_parameter(mysql_parameter,mysql_parameter_value):
    try:
        back_path = "/tmp/mysqlConfig_back"
        if sys.platform.startswith('linux'):
            file_path1 = "/etc/my.cnf"
            file_path2 = "/etc/mysql/my.cnf"
            file_path = None
            if not mysql_parameter in default_mysql_parameter:
                return -10
            
            if not mysql_parameter_value :
                return -20
            
            if os.path.exists(file_path1):
                file_path =file_path1

            if os.path.exists(file_path2):
                file_path = file_path2

            if not file_path:
                return -30
            # 备份
            makedirs(back_path)
            current_data = datetime.datetime.now()
            backfilename = current_data.strftime("%Y%m%d%H%M%S")
            shutil.copy(file_path, os.path.join(back_path, backfilename))

            #更改配置文件
            temp_file_path = file_path + '.tmp'
            with open(file_path,'r') as file:
                lines = file.readlines()
            with open(file_path, 'r') as file, open(temp_file_path, 'w') as temp_file:
                for line in file:
                    if mysql_parameter not in line:
                        temp_file.write(line)
                new_mysql_parameter = mysql_parameter + ' = ' + mysql_parameter_value + '\n'
                temp_file.write(new_mysql_parameter)
            shutil.move(temp_file_path, file_path)
            return 1
        elif sys.platform.startswith('darwin'):
          return -50
        elif sys.platform.startswith('win32'):
          return -50
    except Exception as e:
      print(e)
      return -40
    return 0


def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


if __name__ == '__main__':
    #设置传入参数
    parser = OptionParser()
    parser.add_option('--mysql_parameter', type=str, dest='mysql_parameter',default="")
    parser.add_option('--mysql_parameter_value', type=str, dest='mysql_parameter_value',default="")
    #获取传入参数
    (options, args) = parser.parse_args()
    mysql_parameter = options.mysql_parameter
    mysql_parameter_value = options.mysql_parameter_value
    result = upd_mysql_parameter(mysql_parameter,mysql_parameter_value)
    print(result)