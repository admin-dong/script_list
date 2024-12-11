##send message
APPID='demo-0.0.1-SNAPSHOT.war'
RUNINFO="java -jar ${APPID},port:8080"
JENKINS='http://192.168.17.135:9090'
TITLE='构建信息推送(1)'
MEMOTEXT=""
PY3PATH="/usr/local/python3/bin/python3"
PYFILE='pushlog-1.py'
CURDIR="/opt/build/${JOB_NAME}"
SCRIPTDIR="${CURDIR}/script"
LOG_TEXT="${JENKINS}/job/${JOB_NAME}/${BUILD_NUMBER}/consoleText"
mkdir -p ${SCRIPTDIR}
 
##python_file
cat >${SCRIPTDIR}/${PYFILE}<<EOF
#!/usr/local/python3/bin/python3
# _*_coding:utf-8 _*_
import sys, requests,datetime
#subject = str(sys.argv[1])
#message = str(sys.argv[2])
site="${JENKINS}"
build_time=str(datetime.datetime.now())
build_number="${BUILD_NUMBER}"
build_log_status="${LOG_TEXT}"
build_url="${JOB_NAME}${TITLE}"
build_job="编译${JOB_NAME}"
build_name="编译${JOB_NAME}并部署运行${APPID}"
build_imgname="${APPID}"
build_c_appname="${APPID}"
build_c_runname="${RUNINFO}"
build_c_msg="${MEMOTEXT}"
message="## "+build_url +"通知\n"
message+=">Jenkins站点:<font color='info'>" + site + "</font>\n"
message+=">构建时间:<font color='info'>" + build_time +"</font>\n"
message+=">构建任务:<font color='info'>" + build_job + "</font>\n"
message+=">构建id号:<font color='info'>" + build_number + "</font>\n"
message+=">任务名称:<font color='info'>" + build_name + "</font>\n"
message+=">构建输出:<font color='warning'>" + build_log_status + "</font>\n"
message+=">应用名称:<font color='warning'>" + build_c_appname + "</font>\n"
message+=">启动方式:<font color='warning'>" + build_c_runname + "</font>\n"
message+=">备注说明:<font color='warning'>" + build_c_msg + "</font>\n"

robot = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=46f1202c-2f85-45fa-8e73-769ea9e4b4f6"
#robot = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=" + sys.argv[3]

data = {
    "msgtype": "markdown",
    "markdown": {
        "content":  message
    }
}

response = requests.post(url=robot, json=data)

print(response.json())
EOF

chmod a+x  ${SCRIPTDIR}/${PYFILE}

${PY3PATH} -u   ${SCRIPTDIR}/${PYFILE}