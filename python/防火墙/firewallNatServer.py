# -*- coding: UTF-8 -*-`
import re
import sys
import json
import socket
from time import sleep
from optparse import OptionParser
from paramiko import SSHClient, AutoAddPolicy
from pyDes import *
from binascii import a2b_hex


defaultencoding = 'gbk'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)

def exec_cmd(ip, user, pwd, cmds):
    echoStr = ''
    try:
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.connect(ip, port=22, username=user,
                    password=pwd, timeout=15, compress=True)
        try:
            chan = ssh.invoke_shell()
            chan.settimeout(15)
            sleep(1)
            x = chan.recv(2048).decode('gbk').split('\n')[-1]
            for cmd in cmds:
                chan.send(cmd.encode())
                if cmd[-1] != '\r' or cmd[-1] != '\n':
                    chan.send(chr(13))
                # sleep(3)
                num = 0
                while True:
                    try:
                        ret = str(chan.recv(40960).decode('gbk'))
                    except socket.timeout:
                        echoStr += '\n time out '
                        print('exec {} recv result 15s time out...'.format(cmd))
                        break
                    ret_list = ret.split('\n')
                    # print(ret_list[-1])
                    if re.search(r'---- More ----', ret_list[-1]):
                        echoStr += ret
                        chan.send(chr(32))
                        sleep(0.1)
                        continue
                    elif ret_list[-1].find(x) != -1:
                        echoStr += ret
                        break
                    elif ret_list[-1].find('return') == 0:
                        echoStr += ret
                        chan.send(chr(113))
                        break
                    else:
                        echoStr += ret
            chan.close()
        except Exception as e:
            raise Exception(e)
        finally:
            ssh.close()
    except Exception as e:
        raise Exception(e)
    finally:
        return echoStr

def main(ip, user, pwd):
    belongto = exec_cmd(ip, user, pwd, cmds=['display esn'])
    belongto = re.search(r"(?<=ESN of master:).*(?=\r\n)", belongto).group(0).decode('gbk').encode('utf-8')#获取序列号

    allinfo = exec_cmd(ip, user, pwd, cmds=['dis nat server'])
    newinfo = allinfo.replace('  ---- More ----[42D                                          [42D','')
    spli  = newinfo.split('\r\n\r\n ')
    li = list()
    for i in spli:
        dic = dict()
        
        noblankspace = i.replace(' ','')
        #映射名称
        serverName = re.search(r"(?<=servername:).*(?=\r\n)", noblankspace)
        if serverName:
            dic['serverName'] = serverName.group(0).decode('gbk').encode('utf-8')
        #策略id
        id = re.search(r"(?<=id:).*(?=zone)", noblankspace)
        if id:
            dic['id'] = id.group(0).decode('gbk').encode('utf-8')
        #公网地址
        lobalendaddr = re.search(r"(?<=lobal-end-addr:).*(?=\r\n)", noblankspace)
        if lobalendaddr:
            dic['publicAddress'] = lobalendaddr.group(0).decode('gbk').encode('utf-8')
        #私网地址
        insideendaddr = re.search(r"(?<=inside-end-addr:).*(?=\r\n)", noblankspace)
        if insideendaddr:
            dic['privateAddress'] = insideendaddr.group(0).decode('gbk').encode('utf-8')
        #协议
        protocol = re.search(r"(?<=protocol:).*(?=\r\n)", noblankspace)
        if protocol:
            dic['protocol'] = protocol.group(0).decode('gbk').encode('utf-8')
        #公网端口
        globalendport = re.search(r"(?<=global-end-port:).*(?=\r\n)", noblankspace)
        if globalendport:
            dic['publicPort'] = globalendport.group(0).decode('gbk').encode('utf-8')
        #私网端口
        insideendport = re.search(r"(?<=inside-end-port:).*(?=\r\n)", noblankspace)
        if insideendport:
            dic['privatePort'] = insideendport.group(0).decode('gbk').encode('utf-8')
        dic['sn'] = belongto
        dic['onlyNum'] = belongto + dic['id']
        dic['valueMethod'] = 'auto'
        dic['valueMethodAdd'] = ip
        dic['dataStatus'] = 'effective'
        li.append(dic)
    endic = dict()
    endic['CIT_firewallServerMapping']  = li
    print(json.dumps(endic,ensure_ascii=False)) 
    


def des_decrypt(message):
    k = des('shdevopsshdevops', ECB, padmode=PAD_PKCS5)
    try:
        result = k.decrypt(a2b_hex(message)).decode('utf8')
    except Exception:
        sys.stderr.write('decrypt failed')
        exit(-1)
    else:
        return result


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--host_ip', type=str, dest='host_ip',default='10.1.2.254')
    parser.add_option('--user', type=str, dest='user', default='admin')
    parser.add_option('--pwd', type=str, dest='pwd', default='shmz8866.gw')
    parser.add_option('--fwtype', type=str, dest='fwtype',default='huawei_firewall')

    (options, args) = parser.parse_args()
    host_ip = options.host_ip
    user = options.user
    pwd = des_decrypt(options.pwd)
    #pwd = options.pwd
    fwtype = options.fwtype
    if fwtype == 'huawei_firewall':
        main(host_ip, user, pwd)
    else:
        print('no this type')