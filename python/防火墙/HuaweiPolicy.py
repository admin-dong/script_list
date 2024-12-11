#-*- coding: utf-8 -*-

import re
import sys
import IPy
import json
import socket
#import netaddr
import traceback
from time import sleep
from pyDes import *
from binascii import a2b_hex
from optparse import OptionParser
from paramiko import SSHClient, AutoAddPolicy


defaultencoding = 'gbk'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)

def mask2prefix(mask, netbit=1):
    bin_mask = IPy.IP(mask).strBin()
    re_bin_prefix = re.match('{}+'.format(netbit), bin_mask)
    if re_bin_prefix:
        return len(re_bin_prefix)
    else:
        return

def get_conf_border(txt):
    try:
        endpoint = txt.find('#')
        return txt[:endpoint]
    except:
        print(traceback.format_exc())

def parse_ip_address(spl_address_set):
    address_set = {}
    for item in spl_address_set:
        conf_block = get_conf_border(item)
        lines = conf_block.split('\r\n')
        typeobject_idx = lines[0].find('type object')
        address_name = lines[0][:typeobject_idx].strip()
        address_list = []  # format [0.0.0.0/0, 0.0.0.0-255.255.255.255]
        for line in lines[1:]:
            spl_line = line.strip().split()
            if spl_line and spl_line[0].strip() == 'address':
                if re.match('\d+$', spl_line[1].strip()):
                    idx = spl_line[1].strip()
                if re.match('(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', spl_line[2].strip()):
                    ip = spl_line[2].strip()
                    if spl_line[3].strip() == '0':
                        mask = spl_line[3].strip()
                    elif spl_line[3].strip() == 'mask':
                        if re.match('\d{1,2}$', spl_line[4].strip()) and (int(spl_line[4].strip()) in range(33)):
                            mask = spl_line[4].strip()
                        elif re.match('(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', spl_line[4].strip()):
                            mask = mask2prefix(spl_line[4].strip(), 1)
                        else:
                            # print('mask format Error, line:{}'.format(line))
                            continue
                    elif re.match('(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', spl_line[3].strip()):
                        mask = mask2prefix(spl_line[3].strip(), 0) # wildcard to mask to prefix
                    else:
                        # print('line.3 format Error:addressName {}; line {}'.format(address_name, line))
                        continue
                    if ip and mask:
                        address = '{}/{}'.format(ip, mask)
                        address_list.append(address)
                    else:
                        # print('address format Error, line:{}'.format(line))
                        continue
                elif spl_line[2].strip() == 'range':
                    start_IP = re.match('(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', spl_line[3].strip())
                    end_IP = re.match('(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', spl_line[4].strip())
                    if start_IP and end_IP:
                        start_IP = start_IP.group()
                        end_IP = end_IP.group()
                        # address = netaddr.IPRange(start_IP, end_IP).cidrs()
                        address = '-'.join(start_IP, end_IP)
                        address_list.extend(address)
                    else:
                        # print('start_IP or end_IP is None, line: {}'.format(line))
                        continue
                else:
                    # print('line.2 format Error, line: {}'.format(line))
                    continue
        if address_list:
            address_set[address_name] = address_list
        else:
            print('{} address set is None, conf_block:\n{}'.format(address_name ,conf_block))
    return address_set

def parse_domain_name(spl_domain_name):
    domain_set = {}
    spl_domain_name[-1] = get_conf_border(spl_domain_name[-1])
    for item in spl_domain_name:
        lines = item.split('\r\n')
        domain = []
        domain_set_name = lines[0].strip()
        for line in lines[1:]:
            if line.find('add domain ') != -1:
                domain.append(line[line.find('add domain ')+11:].strip())
        domain_set[domain_set_name] = domain
    return domain_set

def parse_ip_service(spl_service_set):
    service_set = {}
    for item in spl_service_set:
        conf_block = get_conf_border(item)
        lines = conf_block.split('\r\n')
        typeobject_idx = lines[0].find('type object')
        service_name = lines[0][:typeobject_idx].strip()
        service_list = []
        for line in lines[1:]:
            spl_line = line.split()
            if spl_line and spl_line[0].strip() == 'service':
                if re.match('\d+$', spl_line[1].strip()):
                    idx = spl_line[1].strip()
                if spl_line[2].strip() == 'protocol':
                    protocol = spl_line[3].strip()
                    if 'source-port' in spl_line:
                        src_port_idx = spl_line.index('source-port')
                        if len(spl_line[src_port_idx:]) >= 4 and spl_line[src_port_idx + 2] == 'to':
                            src_port = ' '.join(spl_line[src_port_idx+1: src_port_idx+4])
                        elif len(spl_line[src_port_idx:]) >= 2:
                            src_port = spl_line[src_port_idx+1]
                        else:
                            # print('src_port format Error,line: {}'.format(line))
                            src_port = ''
                    if 'destination-port' in spl_line:
                        dst_port_idx = spl_line.index('destination-port')
                        if len(spl_line[dst_port_idx:]) >= 4 and spl_line[dst_port_idx + 2] == 'to':
                            dst_port = ' '.join(spl_line[dst_port_idx+1: dst_port_idx + 4])
                        elif len(spl_line[dst_port_idx:]) >= 2:
                            dst_port = spl_line[dst_port_idx+1]
                        else:
                            print('dst_port format Error,line: {}'.format(line))
                            dst_port = ''
                    service_list.append({'protocol':protocol,
                                         'srcPort': src_port,
                                         'dstPort': dst_port})
        service_set[service_name] = service_list
    return service_set

def parse_rule_name(spl_rule_name, d_address_set, d_service_set, d_domain_name, manageIP):
    datelist = list()
    spl_rule_name[-1] = get_conf_border(spl_rule_name[-1])
    for item in spl_rule_name:
        lines = item.split('\r\n')
        rule_name = lines[0].strip()
        rule_conf = {}
        rule_conf['name'] = rule_name
        rule_conf['id'] = rule_name
        rule_conf['hostip'] = manageIP
        rule_conf['srcaddr'] = []
        rule_conf['dstaddr'] = []
        rule_conf['srcPort'] = []
        rule_conf['dstport'] = []
        for line in lines[1:]:
            try:
                spl_line = line.split()
                if not spl_line:
                    continue
                if spl_line[0].strip() == 'source-zone':
                    rule_conf['srczone'] = spl_line[1].strip()
                elif spl_line[0].strip() == 'destination-zone':
                    rule_conf['dstzone'] = spl_line[1].strip()
                elif spl_line[0].strip() == 'source-address':
                    if spl_line[1].strip() == 'address-set':
                        if re.match('(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', spl_line[2].strip()):
                            ip = re.match('(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', spl_line[2]).group()
                            if re.match('\d+$', spl_line[3].strip()):
                                mask = spl_line[3].strip()
                            elif spl_line[3].strip() == 'mask':
                                if re.match('\d{1,2}$', spl_line[4].strip()) and (int(spl_line[4].strip()) in range(33)):
                                    mask = spl_line[4].strip()
                                elif re.match('(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', spl_line[4].strip()):
                                    mask = mask2prefix(spl_line[4].strip(), 1)
                                else:
                                    # print('rule.srcaddr.mask format Error, line:{}'.format(line))
                                    continue
                            elif re.match('(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', spl_line[3].strip()):
                                mask = mask2prefix(spl_line[3].strip(), 0) # wildcard to mask to prefix
                            else:
                                # print('src.addr.line.3 format Error:addressName {}; line {}'.format(address_name, line))
                                continue
                            if ip and mask:
                                address = '{}/{}'.format(ip, mask)
                                rule_conf['srcaddr'].append(address)
                            else:
                                # print('src.address format Error, line:{}'.format(line))
                                continue
                        else:
                            # address-set后为 address-set-name, 去d_address_set查询地址列表extend到rule_conf['srcaddr']里
                            address_set_name = spl_line[2].strip()
                            address_list = d_address_set.get(address_set_name)
                            if address_list:
                                rule_conf['srcaddr'].extend(address_list)
                            else:
                                # print('srcaddr.Service list was not found, line: {}'.format(line))
                                continue
                    elif spl_line[1].strip() == 'range':
                        start_IP = re.match('(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', spl_line[2].strip())
                        end_IP = re.match('(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', spl_line[3].strip())
                        if start_IP and end_IP:
                            start_IP = start_IP.group()
                            end_IP = end_IP.group()
                            # address = netaddr.IPRange(start_IP, end_IP).cidrs()
                            address = '-'.join(start_IP, end_IP)
                            rule_conf['srcaddr'].extend(address)
                        else:
                            # print('rule.scraddr.range.start_IP or end_IP is None, line: {}'.format(line))
                            continue
                    elif spl_line[1].strip() == 'domain-set':
                        domain_set = spl_line[2].strip()
                        domain = d_domain_name.get(domain_set)
                        if domain:
                            rule_conf['srcaddr'].extend(domain)
                        else:
                            rule_conf['srcaddr'].append(domain_set)
                    elif spl_line[1].strip() == 'any':
                        rule_conf['srcaddr'].append('any')
                    else:
                        print('rule.source-address format Error, line: {}'.format(line))
                elif spl_line[0].strip() == 'destination-address':
                    if spl_line[1].strip() == 'address-set':
                        if re.match('(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', spl_line[2].strip()):
                            ip = re.match('(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', spl_line[2].strip()).group()
                            if re.match('\d+$', spl_line[3].strip()):
                                mask = spl_line[3].strip()
                            elif spl_line[3].strip() == 'mask':
                                if re.match('\d{1,2}$', spl_line[4].strip()) and (int(spl_line[4].strip()) in range(33)):
                                    mask = spl_line[4].strip()
                                elif re.match('(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', spl_line[4].strip()):
                                    mask = mask2prefix(spl_line[4].strip(), 1)
                                else:
                                    # print('rule.dstaddr.mask format Error, line:{}'.format(line))
                                    continue
                            elif re.match('(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', spl_line[3].strip()):
                                mask = mask2prefix(spl_line[3].strip(), 0) # wildcard to mask to prefix
                            else:
                                print('dstaddr.line.3 format Error:addressName {}; line {}'.format(address_name, line))
                                continue
                            if ip and mask:
                                address = '{}/{}'.format(ip, mask)
                                rule_conf['dstaddr'].append(address)
                            else:
                                # print('dst.address format Error, line:{}'.format(line))
                                continue
                        else:
                            address_set_name = spl_line[2].strip()
                            address_list = d_address_set.get(address_set_name)
                            if address_list:
                                rule_conf['dstaddr'].extend(address_list)
                            else:
                                # print('dst.Service list was not found, line: {}'.format(line))
                                continue
                    elif spl_line[1].strip() == 'range':
                        start_IP = re.match('(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', spl_line[2].strip())
                        end_IP = re.match('(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', spl_line[3].strip())
                        if start_IP and end_IP:
                            start_IP = start_IP.group()
                            end_IP = end_IP.group()
                            # address = netaddr.IPRange(start_IP, end_IP).cidrs()
                            address = '-'.join(start_IP, end_IP)
                            rule_conf['dstaddr'].extend(address)
                        else:
                            print('rule.scraddr.range.start_IP or end_IP is None, line: {}'.format(line))
                            continue
                    elif spl_line[1].strip() == 'domain-set':
                        domain_set = spl_line[2].strip()
                        domain = d_domain_name.get(domain_set)
                        if domain:
                            rule_conf['dstaddr'].extend(domain)
                        else:
                            rule_conf['dstaddr'].append(domain_set)
                    elif spl_line[1].strip() == 'any':
                        rule_conf['dstaddr'].append('any')
                    else:
                        print('rule.destination-address format Error, line: {}'.format(line))
                elif spl_line[0].strip() == 'service':
                    if spl_line[1].strip() == 'any':
                        rule_conf['dstport'].append('any')
                    else:
                        service_name = ' '.join(spl_line[1:]).strip()
                        service_list = d_service_set.get(service_name)
                        if service_list:
                            # exist Bug, Joined the key service list will need to modify the model
                            for i in service_list:
                                sPort = i.get('srcPort')
                                dPort = i.get('dstPort')
                                proto = i.get('protocol')
                                dPort = '{}{}'.format(proto, dPort)
                                if sPort:
                                    rule_conf['srcPort'].append(sPort)
                                if dPort:
                                    rule_conf['dstport'].append(dPort)
                        else:
                            rule_conf['dstport'].append(service_name)
                elif spl_line[0].strip() == 'action':
                    rule_conf['action'] = spl_line[1].strip()
            except:
                print('{} line: {}'.format(traceback.format_exc(), line))
        output = {'CIT_FWpolicy': rule_conf}
        datelist.append(output['CIT_FWpolicy'])
    output = dict()
    output['CIT_FWpolicy'] = datelist
    print(json.dumps(output, ensure_ascii=False).encode('utf-8'))


def exec_cmd(ip, user, pwd, cmds=['dis current-configuration']):
    echoStr = ''
    try:
        ssh=SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.connect(ip,port=22,username=user,password=pwd,timeout=15,compress=True)
        try:
            chan=ssh.invoke_shell()
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
        except:
            print(traceback.format_exc())
        finally:
            ssh.close()
    except:
        print(traceback.format_exc())
    finally:
        return echoStr

def main(ip, user, pwd):
    cmd_res2 = exec_cmd(ip, user, pwd)
    cmd_res1 = cmd_res2.encode('gbk').decode()
    cmd_res = cmd_res1.replace('---- More ----', '').replace('\b', '').replace('\x1b[42D', '')
    # print cmd_res
    spl_address_set = cmd_res.split('ip address-set ')[1:]
    d_address_set = parse_ip_address(spl_address_set)
    spl_domain_name = cmd_res.split('\r\n domain-set name ')[1:]
    d_domain_name = parse_domain_name(spl_domain_name)
    spl_service_set = cmd_res.split('\r\nip service-set ')[1:]
    d_service_set = parse_ip_service(spl_service_set)
    spl_rule_name = cmd_res.split('rule name ')[1:]
    parse_rule_name(spl_rule_name, d_address_set, d_service_set, d_domain_name, ip)
    # print cmd_res2
    
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--host_ip', type=str, dest='host_ip')
    parser.add_option('--user', type=str, dest='user')
    parser.add_option('--pwd', type=str, dest='pwd')
    (options, args) = parser.parse_args()
    host_ip = options.host_ip
    user = options.user
    pwd = options.pwd
    k = des('shdevopsshdevops', ECB, padmode=PAD_PKCS5)
    pwd =  k.decrypt(a2b_hex(pwd)).decode('utf8')
    main(host_ip, user, pwd)