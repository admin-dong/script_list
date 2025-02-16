#
SimpleHTTPServer是Python 2自带的一个模块，是Python的Web服务器。它在Python 3已经合并到http.server模块中。SimpleHTTPServer在Python 3的用法与在Python 2的用法相似(python3 -m http.server 6789), 本文以Python 2为例。
SimpleHTTPServer有一个特性，如果待共享的目录下有index.html，那么index.html文件会被视为默认主页；如果不存在index.html文件，那么就会显示整个目录列表。


SimpleHTTPServer使用方法
1）进入待分享的目录 
2）执行命令python -m SimpleHTTPServer 端口号 
注意：不填端口号则默认使用8000端口。 
3）浏览器访问该主机的地址：http://IP:端口号/
示例：执行命令


python -m SimpleHTTPServer
