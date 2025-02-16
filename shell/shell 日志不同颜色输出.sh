
LOGPATH='/tmp/es/install-es.log'

function LOGGER(){
    if [ ! -d ${LOGPATH} ]
    then
        touch ${LOGPATH}
    fi
    LEVEL=${1}
    OUTPUT=${2}
    echo "$(date +'%Y/%m/%d%h:%M:%S') ==> ${LEVEL}: ${OUTPUT}"  >> ${LOGPATH}
}

function ERROR(){
    OUTPUT=${1}
    echo -e "\033[31m ==> [ ${OUTPUT} ] \033[0m"
    LOGGER ERROR "${OUTPUT}"
    LOGGER ERROR "===== Stop next steps ====="
    exit -1
}

function WARNING(){
    OUTPUT=${1}
    echo -e "\033[33m ==> [ ${OUTPUT} ] \033[0m"
    LOGGER WARNING "${OUTPUT}"
}

function INFO(){
    OUTPUT=${1}
    echo -e "\033[32m ==> [ ${OUTPUT} ] \033[0m"
    LOGGER INFO "${OUTPUT}"
}

function GETPACKAGENAME(){
    FILENAME=${1}
    echo ${FILENAME}|sed 's#\.tar\.gz##'|sed 's#\.tgz##'|sed 's#\.zip##'|sed 's#\.rar##'|sed 's#\.jar##'|sed 's#\.tar##'|sed 's#\.jar##'
}