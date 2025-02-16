#!/bin/bash

source /etc/profile

LOGDIR="/var/log/sockets/"
FNAME="p_sockets.log"
ZIPFNAME="$(cat /etc/machine-id)_${FNAME}_$(date -d '-1 days' +'%Y%m%d').zip"

function createDir() {
        [ ! -d ${LOGDIR} ] && mkdir -p ${LOGDIR}
}

function sockets() {
        echo "######### $(date +'%Y-%m-%d %H:%M:%S') #########" >>${LOGDIR}${FNAME}
        ss -at >>${LOGDIR}${FNAME}
        echo -e "\n" >>${LOGDIR}${FNAME}
}

function logRotate() {
        hm=$(date +"%H%M")
        expire=200
        if [[ ${hm} == '0000' ]];then
                cd ${LOGDIR}
                zip ${ZIPFNAME} ${FNAME} -9 && rm -f ${FNAME}
                systemsize=$(df | grep -w '/' | awk '{print $2}')
                if [[ ${systemsize} -lt 80000000 ]];then
                        expire=30
                fi
                find ${LOGDIR} -type f -mtime +${expire} -name "*log*" | xargs rm -f 
                /opt/scripts/upload_cos -f ${ZIPFNAME}
        fi
        
}

function main() {
        createDir
        logRotate
        sockets
}

main


#周期性地记录系统中TCP套接字的状态，并将记录的日志文件进行压缩归档和上传。