# python 怎么开启 https 的 web 服务

开启为了简单通过 web 方式看目录下东西。

## python2
----

### 如果是开启 http: 
用下面即可：
```
python -m SimpleHTTPServer $listen_port
```

### 如是 https：
可以用下面
```
import BaseHTTPServer, SimpleHTTPServer
import ssl

httpd = BaseHTTPServer.HTTPServer(('localhost', $listen_port), SimpleHTTPServer.SimpleHTTPRequestHandler)
httpd.socket = ssl.wrap_socket(httpd.socket, certfile='path/to/cert.pem', keyfile='path/to/key.pem', server_side=True)

print 'Serving HTTPS on port $listen_port ...'
httpd.serve_forever()
```

需要用下面命令生成 cert.pem 与 key.pem
```
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365
```
中间提示填一堆信息，可随便填。有个 PEM，需要记住填了什么，需要至少4位长。在启动上面脚本的时候，要求你填这个码。

上面验证通过。

## python3
----
```
from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl

httpd = HTTPServer(('localhost', $listen_port), SimpleHTTPRequestHandler)
httpd.socket = ssl.wrap_socket(httpd.socket,
                               server_side=True,
                               certfile='path/to/cert.pem',  # 指向你的证书文件路径
                               keyfile='path/to/key.pem',    # 指向你的私钥文件路径
                               ssl_version=ssl.PROTOCOL_TLS)

print('Serving HTTPS on port $listen_port...')
httpd.serve_forever()
```
暂没验证。
