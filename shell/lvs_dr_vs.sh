#!/bin/bash

vip='10.0.0.100'
iface='lo:1'
mask='255.255.255.255'
port='80'
rs1='10.0.0.18'
rs2='10.0.0.28'
scheduler='wrr'
type='-g'
rpm -q ipvsadm &> /dev/null || yum -y install ipvsadm &> /dev/null

case $1 in
start)
    ifconfig $iface $vip netmask $mask #broadcast $vip up
    iptables -F
 
    ipvsadm -A -t ${vip}:${port} -s $scheduler
    ipvsadm -a -t ${vip}:${port} -r ${rs1} $type -w 1
    ipvsadm -a -t ${vip}:${port} -r ${rs2} $type -w 1
    echo "The VS Server is Ready!"
    ;;
stop)
    ipvsadm -C
    ifconfig $iface down
    echo "The VS Server is Canceled!"
    ;;
*)
    echo "Usage: $(basename $0) start|stop"
    exit 1
    ;;
esac
