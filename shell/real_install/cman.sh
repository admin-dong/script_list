#!/bin/bash

URL=https://storage.googleapis.com/google-code-archive-downloads/v2/code.google.com/manpages-zh/manpages-zh-1.5.1.tar.gz


FILE=`basename $URL`


wget $URL

if [ ! -e $FILE ];then

	echo "down $FILE fail!"
	exit 1
fi


source /etc/os-release

if [ $NAME = 'Ubuntu' ];then 
	apt install -y gcc make
else
	yum install -y gcc make
fi


tar xf $FILE
cd `basename $FILE .tar.gz`

./configure --disable-zhtw
make && make install


if [ $? -ne 0 ];then
	echo -e "\n\n======================== install fail =============================\n\n"

	exit 1
fi


aliasFile="/etc/bashrc"

if [ $NAME = 'Ubuntu' ];then 
	aliasFile="/etc/bash.bashrc"
fi

echo "alias cman='man -M /usr/local/share/man/zh_CN/'" >> ${aliasFile}

echo -e "\n\n======================== install success ===============================================\n"

echo -e "\n\n======================== please run 'source ${aliasFile}' ==============================\n"

echo -e "============================ you can run 'cman bash' test ==================================\n"