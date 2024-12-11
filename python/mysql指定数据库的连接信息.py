# -*- coding: UTF-8 -*-
'''
pip install mysql-connector-python
serverIP 数据库链接ip
serverUser 数据库用户名
serverPasswd 数据库密码
'''

import json
import requests
from pyDes import *
from binascii import a2b_hex
from optparse import OptionParser
import warnings
import mysql.connector
from mysql.connector import Error
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

def des_decrypt(message):
    k = des('devopsdevops', ECB, padmode=PAD_PKCS5)
    return k.decrypt(a2b_hex(message)).decode('utf8')



def get_mysql_parameter(host, database, user, password):
    try:
        mysql_parameter_online = {}
        connection = mysql.connector.connect(host=host,
                                             database=database,
                                             user=user,
                                             password=password)
        if connection.is_connected():
            cursor = connection.cursor()
            for key,value in default_mysql_parameter.items():
                
                cursor.execute(f"SHOW VARIABLES LIKE '{key}';")
                result = cursor.fetchone()
                if result :
                  mysql_parameter_online[key] = result[1]
            cursor.close()
            return mysql_parameter_online
    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection:
            connection.close()


if __name__ == '__main__':
    #设置传入参数
    parser = OptionParser()
    parser.add_option('--serverIP', type=str, dest='serverIP',default="172.0.0.1")
    parser.add_option('--serverUser', type=str, dest='serverUser',default="")
    parser.add_option('--serverPasswd', type=str,dest='serverPasswd', default='')
    #获取传入参数
    (options, args) = parser.parse_args()
    serverIP = options.serverIP
    serverUser = options.serverUser
    #serverPasswd = des_decrypt(options.serverPasswd)
    serverPasswd = options.serverPasswd
    result = get_mysql_parameter(serverIP,"sys",serverUser,serverPasswd)
    print(json.dumps(result))