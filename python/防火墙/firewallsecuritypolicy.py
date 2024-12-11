# -*- coding: UTF-8 -*-`
import re
import sys
import json
import socket
import copy
import requests
from time import sleep
from optparse import OptionParser
from paramiko import SSHClient, AutoAddPolicy
from pyDes import *
from binascii import a2b_hex


defaultencoding = 'gbk'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)

def deldata(ip):
    url = 'http://cmdb.bestwehotel.io/delcmdb/citFieldsInfo/deleteTable/direct'
    header = {
        "Content-Type": "application/json",
        "Cookie": "DefaultLanguage=zh-CN; sessionid=404e36b7d3604d55ab0d5b4567d81023; token==OL6NJIB+EtSO3E8UOtbizXdrQ8BLm/mDJDhqos1z+RsEqk4bWnEAPpx2Y1GlDwWf9Fflhak81H1rJ7XHF9Qi9Z+SaclCHrUiu3MJvr19/oFoQNbpWAMoJP0ZM9oa9r1h0wQm/3+dbUxttlWLngkFuw=="
    }
    body = {
        "dataBase": "cmdb",
        "tableName": "firewallpolicy",
        "conditions": [
            {
                "name": "hostip",
                "condition": "eq",
                "value": ip}
        ],
        "dropKey": "Qye6B3T"
    }
    back = requests.post(url=url, data=json.dumps(body), headers=header)
    return back.text



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

def securitypolicy(security,ip,belongto,sysname):
    
    securitypolicyBackinfo = security.decode('gbk').encode('utf-8')
    securitypolicyTrueinfo = securitypolicyBackinfo.split('-------------------------------------------------------------------------------')
    securitypolicyTrueinfo = securitypolicyTrueinfo[1].split('\r\n')
    del securitypolicyTrueinfo[-1]
    del securitypolicyTrueinfo[0]
    securityPolicyli = []
    for sp in securitypolicyTrueinfo:
        dic = dict()
        newsp = sp.split(' ')
        datalist = [x.strip() for x in newsp if x.strip()!='']
        dic['poliID'] = datalist[0]
        dic['Name'] = datalist[1]
        dic['policyStatus'] = datalist[2]
        dic['Action'] = datalist[3]
        dic['Hitcnt'] = datalist[4]
        dic['onlyNum'] = ip+datalist[0]
        dic['belongDevice'] = belongto
        dic['hostName'] = sysname
        dic['hostIP'] = ip
        dic['valueMethod'] = 'auto'
        dic['valueMethodAdd'] = ip
        dic['dataStatus'] = 'effective'
        securityPolicyli.append(dic)
    return securityPolicyli

def get_detailinfo(allinfo):
    spinfo = None
    outdata = allinfo.split('#')
    for sp in outdata:
        if 'security-policy' in sp:
            spinfo=sp
    spdata = spinfo.replace('---- More ----\x1b[42D                                          \x1b[42D','')
    spdata = spdata.split('\r\n rule name ')
    spdata.pop(0)
    endli = list()
    for detail in spdata:
        dic = dict()
        #防火墙策略名称
        spname = re.search(r"(?<=).*(?=\r\n)", detail).group(0)
        dic['Name'] = spname.decode('gbk').encode('utf-8')
        #描述
        description= re.search(r"(?<=description ).*(?=\r\n)", detail)
        if description:
            dic['description'] = description.group(0).decode('gbk').encode('utf-8')
        #源安全区域
        sourcezone  = re.findall(r'source-zone (.*?)\r\n',detail)
        if sourcezone != []:
            dic['sourcezone'] = [i.decode('gbk').encode('utf-8') for i in sourcezone]
        else:
            dic['sourcezone'] = ['any']
        #目的安全区域
        destinationzone = re.findall(r'destination-zone (.*?)\r\n',detail)
        if destinationzone != []:
            dic['destinationzone'] = [i.decode('gbk').encode('utf-8') for i in destinationzone]
        else:
            dic['destinationzone'] = ['any']
        #源地址/地区
        sourceaddress = re.findall(r'source-address (.*?)\r\n',detail)
        if sourceaddress != []:
            dic['sourceaddress'] = [i.decode('gbk').encode('utf-8') for i in sourceaddress]
        else:
            dic['sourceaddress'] = ['any']
        #目的地址/地区
        destinationaddress = re.findall(r'destination-address (.*?)\r\n',detail)
        if destinationaddress != []:
            dic['destinationaddress'] = [i.decode('gbk').encode('utf-8') for i in destinationaddress]
        else:
            dic['destinationaddress'] = ['any']
        #服务
        service = re.findall(r'service (.*?)\r\n',detail)
        if service != []:
            dic['service'] = [i.decode('gbk').encode('utf-8') for i in service]
        else:
            dic['service'] = ['any']
        endli.append(dic)
    return endli

def natpolicy(nat,ip,belongto,sysname):
    natpolicyBackinfo = nat.decode('gbk').encode('utf-8')
    natpolicyTrueinfo = natpolicyBackinfo.split('-------------------------------------------------------------------------------')
    natpolicyTrueinfo = natpolicyTrueinfo[1].split('\r\n')
    del natpolicyTrueinfo[-1]
    del natpolicyTrueinfo[0]
    natPolicyli = []
    for np in natpolicyTrueinfo:
        dic = dict()
        nat = np.split(' ')
        datalist = [x.strip() for x in nat if x.strip()!='']
        dic['poliID'] = datalist[0]
        dic['Name'] = datalist[1]
        dic['policyStatus'] = datalist[2]
        dic['Action'] = datalist[3]
        dic['Hitcnt'] = datalist[4]
        dic['onlyNum'] = ip+datalist[0]
        dic['belongDevice'] = belongto
        dic['hostName'] = sysname
        dic['hostIP'] = ip
        dic['valueMethod'] = 'auto'
        dic['valueMethodAdd'] = ip
        dic['dataStatus'] = 'effective'
        natPolicyli.append(dic)
    return natPolicyli

def main(ip, user, pwd):
    allinfo = exec_cmd(ip, user, pwd, cmds=['dis cu'])
    detailLi = get_detailinfo(allinfo)#详细数据
    sysname = re.search(r"(?<=sysname ).*(?=\r\n)", allinfo).group(0) #获取系统名称
    belongto = exec_cmd(ip, user, pwd, cmds=['display esn'])
    belongto = re.search(r"(?<=ESN of master:).*(?=\r\n)", belongto).group(0)#获取序列号
    #安全策略
    security = exec_cmd(ip, user, pwd, cmds=['dis security-policy  rule all'])
    securitypolicyli = securitypolicy(security,ip,belongto,sysname)
    for se in securitypolicyli:
        for de in detailLi:
            if se['Name'] == de['Name']:
                se.update(de)
    #Nat策略
    nat = exec_cmd(ip, user, pwd, cmds=['dis nat-policy  rule all'])
    natpolicyli = natpolicy(nat,ip,belongto,sysname)
    for se in natpolicyli:
        for de in detailLi:
            if se['Name'] == de['Name']:
                se.update(de)
    gatewayServiceli  = []
    gatewayServiceli.append({
        'manageIP':ip,
        'NETPolicy':natpolicyli,
        'securityPolicy':securitypolicyli,
        'valueMethod' : 'auto',
        'valueMethodAdd' : ip,
        'dataStatus' : 'effective'
    })
    # print(json.dumps(gatewayServiceli,ensure_ascii=False))
    endic = dict()
    endic['CIT_firewallAndGatewayService'] = gatewayServiceli
    endic['CIT_firewallpolicy']  = securitypolicyli
    print(json.dumps(endic,ensure_ascii=False))
    





def cisco_exec_cmd(ip, user, pwd, enablepwd, cmds=['enable'],):
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
                chan.send(enablepwd.encode())
                chan.send(chr(13))
                chan.send('show hostname'.encode())
                chan.send(chr(13))
                chan.send('show access-list'.encode())
                chan.send(chr(13))
                # sleep(3)
                num = 0
                while True:
                    try:
                        ret = str(chan.recv(40960).decode('gbk'))
                    except socket.timeout:
                        echoStr += '\n time out '
                        #print('exec {} recv result 15s time out...'.format(cmd))
                        break
                    ret_list = ret.split('\n')
                    # print(ret_list[-1])
                    if re.search(r'<--- More --->', ret_list[-1]):
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
            raise Exception('ssh error:{}'.format(e))
            exit(1)
            # print {"ssh error":e}
            # print(traceback.format_exc())
        finally:
            ssh.close()
    except Exception as e:
        raise Exception(e)
        # print 'ssh error:{}'.format(e)
        # print(traceback.format_exc())
    finally:
        return echoStr


def cisco_fw(ip, user, pwd,  enablepwd):
    allinfo = cisco_exec_cmd(ip, user, pwd, enablepwd)
    #print "Error:No data was obtained,See SSH connections"
    if not allinfo:
       raise Exception("Error:No data was obtained,See SSH connections")
       exit(1)
    hostname = re.search(r"(?<=hostname\r\n).*(?=\r\n\r)", allinfo).group(0)
    out1 = allinfo.split('#')
    out1.pop(0)
    out1.pop(-1)
    if 'More' in out1[1]:
        outmore = out1[1].replace('<--- More --->\r              \r', '')
    getli = outmore.split('\r\n')
    getli.pop(0)
    getli.pop(-1)
    li = list()
    for po in getli:
        if 'hitcnt' in po:
            dic = dict()
            allpo = po.strip().split(' ')
            dic['id'] = allpo[3]
            dic['overdue'] = 'true'
            dic['brand'] = 'CISCO'
            dic['onlynum'] =ip+'-'+hostname+'-'+allpo[3] + '-' + allpo[-1]
            if 'any' in allpo:
                dic['name'] = allpo[1]
                dic['hostname'] = hostname
                dic['hostip'] = ip
                hit = allpo[-2]
                hitcnt = hit.split('=')
                dic['hitcnt'] = hitcnt[1][:-1]
                dic['action'] = allpo[5]
                src = allpo[1].split('-')
                dic['srczone'] = src[0]
                dic['dstzone'] = src[1]
                if allpo[-3] == 'any' and allpo[-4] == 'any':
                    dic['srcaddr'] = ['any']
                    dic['dstaddr'] = []
                    dic['dstaddrlocal'] = ['any']
                    dic['dstport'] = ['any']
    
                elif allpo[-3] == 'any' and allpo[-4] != 'any':
                    dic['srcaddr'] = allpo[7:9]
                    dic['dstaddr'] = []
                    dic['dstaddrlocal'] = ['any']
                    dic['dstport'] = ['any']
           
         
                elif allpo[-4] == 'any' and allpo[-3] != 'any':
                    dic['srcaddr'] = ['any']
                    dic['dstaddr'] = []
                    dic['dstaddrlocal'] = [allpo[-5]]
                    dic['dstport'] = [allpo[-3]]
                    
                elif allpo[-5] == 'any':
                    dic['srcaddr'] = ['any']
                    dic['dstaddr'] = []
                    dic['dstaddrlocal'] = [allpo[-3]]
                    dic['dstport'] = [allpo[-3]]
                    
                elif allpo[-7] == 'any':
                    dic['srcaddr'] = ['any']
                    dic['dstaddr'] = []
                    dic['dstaddrlocal'] = [allpo[-5]]
                    dic['dstport'] = [allpo[-3]]

                else:
                    dic['srcaddr'] = allpo[7:9]
                    dic['dstaddr'] = []
                    dic['dstaddrlocal'] = [allpo[-5]]
                    dic['dstport'] = [allpo[-3]]
                    
            elif 'range' in allpo:
                dic['name'] = allpo[1]
                # dic['id'] = allpo[3]
                dic['hostname'] = hostname
                dic['hostip'] = ip
                hit = allpo[-2]
                hitcnt = hit.split('=')
                dic['hitcnt'] = hitcnt[1][:-1]
                dic['action'] = allpo[5]
                src = allpo[1].split('-')
                dic['srczone'] = src[0]
                dic['dstzone'] = src[1]
                dic['srcaddr'] = allpo[7:9]
                dic['dstaddr'] = []
                dic['dstaddrlocal'] = [allpo[-6]]
                dic['dstport'] = [allpo[-4:-2]]
                
                
            elif 'object-group' and 'uat_gree_blue' in allpo:
                allpo.pop(6)
                dic['name'] = allpo[1]
                # dic['id'] = allpo[3]
                dic['hostname'] = hostname
                dic['hostip'] = ip
                hit = allpo[-2]
                hitcnt = hit.split('=')
                dic['hitcnt'] = hitcnt[1][:-1]
                dic['action'] = allpo[5]
                src = allpo[1].split('-')
                dic['srczone'] = src[0]
                dic['dstzone'] = src[1]
                dic['srcaddr'] = allpo[7:9]
                dic['dstaddr'] = []
                dic['dstaddrlocal'] = [allpo[-5]]
                dic['dstport'] = [allpo[-3]]
                
            else:
                dic['name'] = allpo[1]
                # dic['id'] = allpo[3]
                dic['hostname'] = hostname
                dic['hostip'] = ip
                hit = allpo[-2]
                hitcnt = hit.split('=')
                dic['hitcnt'] = hitcnt[1][:-1]
                dic['action'] = allpo[5]
                src = allpo[1].split('-')
                dic['srczone'] = src[0]
                dic['dstzone'] = src[1]
                outhost = copy.deepcopy(allpo[7:9])
                if 'host' in outhost:
                    hostindex = outhost.index('host')
                    outhost.pop(hostindex)
                    dic['srcaddr'] = outhost
                    
                else:
                    dic['srcaddr'] = outhost
            
                dic['dstaddr'] = []
                dic['dstaddrlocal'] = [allpo[-5]]
                dic['dstport'] = [allpo[-3]]

            li.append(dic)
    if li:
        code = deldata(ip)
        endic = dict()
        endic['CIT_firewallpolicy'] = li
        print(json.dumps(endic, indent=2))
    else:
        raise Exception('there is no data,pelase check SSH connections')
        exit(1)


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
    parser.add_option('--host_ip', type=str, dest='host_ip',default='')
    parser.add_option('--user', type=str, dest='user', default='')
    parser.add_option('--pwd', type=str, dest='pwd', default='')
    parser.add_option('--eapwd', type=str, dest='eapwd',default='')
    parser.add_option('--fwtype', type=str, dest='fwtype',default='')

    (options, args) = parser.parse_args()
    host_ip = options.host_ip
    user = options.user
    pwd = des_decrypt(options.pwd)
    #pwd = options.pwd
    #eapwd = des_decrypt(options.eapwd)
    eapwd = options.eapwd
    fwtype = options.fwtype
    if fwtype == 'huawei_firewall':
        main(host_ip, user, pwd)
    elif fwtype == 'cisco_firewall':
        cisco_fw(host_ip, user, pwd,  eapwd)
    else:
        print('no this type')