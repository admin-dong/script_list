#!/bin/bash
#
#********************************************************************
#Author:			wangxiaochun
#QQ: 				29308620
#Date: 				2019-07-03
#FileName：			inotify_rsync.sh
#URL: 				http://www.wangxiaochun.com
#Description：		The test script
#Copyright (C): 	2019 All rights reserved
#********************************************************************


SRC='/data/www/'
DEST='rsyncuser@10.0.0.202::backup'

#rpm -q inotify-tools &> /dev/null  ||yum -y install  inotify-tools
#rpm -q rsync &> /dev/null  || yum -y install rsync

inotifywait  -mrq  --exclude=".*\.swp" --timefmt '%Y-%m-%d %H:%M:%S' --format '%T %w %f' -e create,delete,moved_from,moved_to,close_write,attrib ${SRC} |while read DATE TIME DIR FILE;do
        FILEPATH=${DIR}${FILE}
        rsync -az --delete  --password-file=/etc/rsync.pas $SRC $DEST && echo "At ${TIME} on ${DATE}, file $FILEPATH was backuped up via rsync" >> /var/log/changelist.log
done
