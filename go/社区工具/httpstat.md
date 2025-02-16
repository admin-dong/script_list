httpstat

**需求场景**

A 服务调用 B 服务的 HTTP 接口，发现 B 服务返回超时，不确定是网络的问题还是 B 服务的问题，需要排查。

**工具简介**

****

就类似 curl，httpstat 也可以请求某个后端，而且可以把各个阶段的耗时都展示出来，包括 DNS 解析、TCP 连接、TLS 握手、Server 处理并等待响应、完成最终传输等，非常直观。上图：

![img](https://cdn.nlark.com/yuque/0/2024/png/35538885/1716948007204-4c8cbfaf-3ae8-452a-a9bc-fa3009d724f6.png)

看着不错吧，咱们一起测试一下。这个工具是 go 写的，作者没有提供二进制包，所以需要自己编译。

**安装 Go 环境  加载配置文件  **

**使用 **

****

****

****

**安装 httpstat**

```
go install github.com/davecheney/httpstat@latest
go: downloading github.com/davecheney/httpstat v1.1.0
go: downloading golang.org/x/sys v0.0.0-20201223074533-0d417f636930
```

在自己的go 文件目录下面 找到这个包

移动到 /usr/bin 目录下

```
cd /root/go/bin
mv httpstat /usr/bin
```

# httpstat 有哪些参数可用：

```
httpstat --help
Usage: httpstat [OPTIONS] URL

OPTIONS:
  -4 resolve IPv4 addresses only
  -6 resolve IPv6 addresses only
  -E string
     client cert file for tls config
  -H value
     set HTTP header; repeatable: -H 'Accept: ...' -H 'Range: ...'
  -I don't read body of request
  -L follow 30x redirects
  -O save body as remote filename
  -X string
     HTTP method to use (default "GET")
  -d string
     the body of a POST or PUT request; from file use @filename
  -k allow insecure SSL connections
  -o string
     output file for body
  -v print version number

ENVIRONMENT:
  HTTP_PROXY    proxy for HTTP requests; complete URL or HOST[:PORT]
                used for HTTPS requests if HTTPS_PROXY undefined
  HTTPS_PROXY   proxy for HTTPS requests; complete URL or HOST[:PORT]
  NO_PROXY      comma-separated list of hosts to exclude from proxy
```

curl 测试

```
curl -X POST -H "Content-Type: application/json" -d '{"service": "tomcat"}' 'https://httpbin.org/post?name=ulric&city=beijing'
{
  "args": {
    "city": "beijing",
    "name": "ulric"
  },
  "data": "{\"service\": \"tomcat\"}",
  "files": {},
  "form": {},
  "headers": {
    "Accept": "*/*",
    "Content-Length": "21",
    "Content-Type": "application/json",
    "Host": "httpbin.org",
    "User-Agent": "curl/8.4.0",
    "X-Amzn-Trace-Id": "Root=1-6655a6c4-4522374c5b8d68143d638049"
  },
  "json": {
    "service": "tomcat"
  },
  "origin": "123.113.255.104",
  "url": "https://httpbin.org/post?name=ulric&city=beijing"
}
```

把curl 换成httpstat

```
httpstat -X POST -H "Content-Type: application/json" -d '{"service": "tomcat"}' 'https://httpbin.org/post?name=ulric&city=beijing'

Connected to 34.198.16.126:443

HTTP/2.0 200 OK
Server: gunicorn/19.9.0
Access-Control-Allow-Credentials: true
Access-Control-Allow-Origin: *
Content-Length: 529
Content-Type: application/json
Date: Tue, 28 May 2024 09:41:44 GMT

Body discarded

  DNS Lookup   TCP Connection   TLS Handshake   Server Processing   Content Transfer
[     11ms  |         217ms  |        446ms  |            570ms  |             0ms  ]
            |                |               |                   |                  |
   namelookup:11ms           |               |                   |                  |
                       connect:229ms         |                   |                  |
                                   pretransfer:678ms             |                  |
                                                     starttransfer:1248ms           |
                                                                                total:1248ms
```

![img](https://cdn.nlark.com/yuque/0/2024/png/35538885/1716948893795-30032a41-0a5f-47fc-9f2e-e7db563ff7c4.png)