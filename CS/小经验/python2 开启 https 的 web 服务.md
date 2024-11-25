# python2 怎么开启 https 的 web 服务

开启为了简单通过 web 方式看目录下东西。

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

httpd = BaseHTTPServer.HTTPServer(('localhost', 18899), SimpleHTTPServer.SimpleHTTPRequestHandler)
httpd.socket = ssl.wrap_socket(httpd.socket, certfile='path/to/cert.pem', keyfile='path/to/key.pem', server_side=True)

print 'Serving HTTPS on port 18899...'
httpd.serve_forever()
```

需要用下面命令生成 cert.pem 与 key.pem
```
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365
```
中间提示填一堆信息，可随便填。有个 PEM，需要记住填了什么，需要至少4位长。在启动上面脚本的时候，要求你填这个码。
