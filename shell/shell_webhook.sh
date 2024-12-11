#!/bin/bash  
  
# 检查脚本是否接收到了至少一个参数（即消息内容）  
if [ $# -lt 1 ]; then  
    # 如果没有接收到参数，则打印使用方法并退出脚本  
    echo "usage: $0 <message>" >&2  
    # >&2 表示将错误信息输出到标准错误（stderr）  
    exit 1  
fi  
  
# 设置Feishu Webhook的URL  
URL="https://open.feishu.cn/open-apis/bot/v2/hook/0f45db6f-f9b7-4269-a5b1-6cdd29110673"  
  
# 将传入的第一个参数（即消息内容）赋值给变量MSG  
# 使用sed命令将消息中的双引号替换为转义的双引号（\"），这是为了确保JSON格式正确  
MSG=$(echo -n "$1" | sed 's/"/\\"/g')  
# echo $MSG 这行仅用于在终端中显示处理后的消息内容，对脚本功能无影响  
  
# 使用curl命令向Feishu Webhook URL发送POST请求  
# -m 10 表示设置curl的超时时间为10秒  
# -H 'Content-Type:application/json' 设置HTTP请求头为Content-Type: application/json  
# -d 后面跟的是要发送的JSON数据，这里是一个包含msg_type和content字段的JSON对象  
# msg_type设置为"text"，表示消息类型为文本  
# content.text字段设置为之前处理过的消息内容（$MSG）  
curl -m 10 "$URL" -H 'Content-Type:application/json' -d '{"msg_type":"text","content":{"text":"'"$MSG"'"}}'
