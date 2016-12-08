>2016年12月 8日 星期四 11时45分29秒 CST

# Nginx 入门使用教程
Nginx 有一个 master 进程和多个 worker 进程, 其中
- 主进程主要负责 read and evaluate configuration;
- worker 进程处理请求

nginx 采取了事件驱动模型和独立于OS的机制来分发请求给 [worker 进程][0], 
nginx 及其各个模块的运作方式取决于配置文件，默认的配置文件是nginx.conf，此文件放置的路径由如下三种可能

1. 目录 /usr/local/nginx/conf
2. 目录 /etc/nginx
3. 目录 /usr/local/etc/nginx

## Nginx 的功能
Nginx 主要如下五种基本功能：
1. Web server: 配置 virtual servers and locations, 使用变量，重写URIs, 定制error pages
2. Serving static content: 设置请求内容的root directory, 并且 create ordered lists of files to serve if the original index file or 
  URI does not exist
3. Rever proxy: 
  - Proxying requests to HTTP, FastCGI, uwsgi, SCGI, and memcached servers; 
  - 控制 proxied request headers;
  - 缓存 proxied servers 的 responses
4. Compression and decompression: Compressing responses on the fly to minimize use of network bandwidth
5. Web content cache: Caching static and dynamic content from proxied server



## Starting, Stopping, and Reloading Configuration
运行nginx可执行文件，便可以启动nginx, 启动之后, 可以使用如下的语法来控制 nginx 
```bash
$ nginx -s signal
```
其中， -s 指定的 signal 参数的可选范围是：
- stop -- fast shutdown
- quit -- graceful shut down
- reload -- reloading the configuration file
- reopen -- reopening the log files

主进程在接收到重载配置文件的信号后，它首先会检查新的配置文件的语法的正确性，
然后 apply 配置文件中指定的配置。

- 如果配置文件语法正确的话，主进程具体会执行如下操作：
  1. 启动新的 worker 进程，
  2. 发送消息给 old worker process, 要求他们 shut down
- 如果配置有误，则主进程会进行回滚操作，继续使用旧的配置运作

除了使用 nginx 自带的命令来发送信号，还可以借助linux上的工具kill 来发送信号，
不过得指定相应的进程号，nginx 主进程的进程ID `nginx.pid` 默认是放在目录 `/usr/local/nginx/logs` 
或者 `/var/run` 中。比如，主进程号是1628，则发送 QUIT 信号会导致 nginx 的 graceful shutdown, 
```bash
$ kill -s QUIT 1628
```

此外，可以使用ps工具获取nginx 所有在运行的进程，如下：
```bash
$ ps -ax | grep nginx
```

## Configuration File's Structure
nginx 的模块是由配置文件中的指令控制的，指令有两种：
1. Simple Directives: 指令的格式为`name parameters;`
2. Block Directives: 由多条简单指令组成，不过最外层是花括号{}。如果 Block Directives 里面有其他指令的话，
  则称之为 context (比如 [events][1], [http][2], [server][3], [location][4], etc.)

**main context**: 配置文件中在任何的context 之外的指令属于 main context

`events` 和 `http` 指令是位于 `main context`中的，而 `server` 位于 `http` 中，
`location` 位于 `server`中

nginx 配置文件的行注释符是 #


## nginx 配置例子
### Serving Static Content
web server 的一个主要任务就是 serve out files (比如图片或者静态的HTML页面), 下面来实现一个配置使得
- 根据请求的不同，提供不同的文件
  - local directory `/data/www` 中可能放置 HTML 文件
  - local directory `/data/images` 放置图片

要实现这个，

1. 首先需要创建两个目录
  - 目录`/data/www`, 该目录中放置html文件
  - 目录`/data/images`, 该目录中放置图片
2. 然后需要编辑配置文件的相关指令:
set up a `server` block inside the `http` block with tow `location` blocks
```nginx
http {
  server {
    location / {
      root /data/www;
    }
    
    location /images/ {
      root /data;
    }

```
其中， 第一个`location` block 指令的意思是将前缀"/" 与请求中的URI做比较，
[root][5] 的意思是在请求中的URI中加入root中指定的前缀, 比如
- 请求中的URI是`/index.html`，则文件的真实路径是`/data/www/index.html`; 
- 请求中的URI是`/images/cat.png`, 则文件的真实路径是`/data/images/cat.png`.

3. 然后执行下面的命令重载配置文件使得上面的配置生效
```bash
$ nginx -s reload
```


### Setting Up a Simple Proxy Server
nginx 可以用作代理服务器，即nginx 负责接收客户端发送过来的请求，然后转发给the proxied servers, 
然后获取这些proxied servers的响应，最后再转发给客户端。

下面配置一个基本的代理服务器，能够完成如下的任务：
- serve requests of images with files from the local directory
- send all other requests to a proxied server

具体配置如下，这个 server 会过滤出所有以.gif, .jpb, .png结尾的URI的请求，并将它们映射到目录`/data/images/`下（这个是
通过把请求的URI添加到`root`指令的参数后面实现的), 然后把素有其他的请求都转发给下面配置中的 the proxied server.
```nginx
http {
  server {
    listen 8080;
    root /data/up1;

    location / {
      proxy_pass http://localhost:8080/;
    }
    location ~ \.(gif|jpg|png)$ {
      root /data/images;
    }
}
```
#### nginx proxy_pass 指令
其中的 [`proxy_pass URL;`][6] 指令表示设置被代理的服务器的 protocol, address and an optional URI , 
该参数指定了location会被映射到何处.
1. 协议protocol部分，可以指定`http`或者`https`，
2. 地址address有两种方式：
- 可以表示为a domain name or IP address, and an optional port
```nginx
proxy_pass http://localhost:8080/uri/;
```
- 或者表示为 UNIX-domain socket path specified after the word "unix" and enclosed in colons:
```nginx
proxy_pass http://unix:/tmp/backend.socket:/uri/;
```

#### nginx location 指令
nginx 在选择一个 location block 来 serve a request 时，nginx 首先会逐条检查指定了具体前缀的 [location 指令][4], 并记住具有最长前缀的 `location`, 
然后再检查指定正则表达式的location。如果存在跟正则表达式匹配的`location`, 则nginx 会采用这条`location`指令，否则会选取之前记住的`location`

location 指令的语法是
```nginx
location [ = | ~ | ~* | ^~ ] uri {...}

location @name {...}
```
第一种 location 指令需要嵌套使用在块指令 `server` 和 `location` context 中，
location 的定义可以是 a prefix string 或者 a regular expression
- 如果是 prefix string, 则前面可以不用加修饰符，或者加上修饰符 `= ` 、`^~ `
  - `= ` 表示请求中的URI 和 location 中指定的要完全匹配
  - `^~ ` 表示如果该 prefix location 是 最长的匹配的, 则nginx 不会再继续去检查正则表达式, 😁，这个可以用来加快请求的处理速度
- 如果是正则表达式，则前面需要加上修饰符 `~*` 或者 ` ~ ` 
  - `~*` 表示正则表达式匹配的时候是 case-insensitive 的
  - `~ ` 表示匹配的时候是 case-sensitive 的

而第二种 location 指令中的 `@name` 表示这会定义一个名字为`name`的location, 此种 location 是不会用作常规的请求处理的，
而是用来重定向请求的，注意他们也不可以被嵌套使用，也不可以包含其他location指令.


下面举例，假设配置文件中指定了如下5种location：
```nginx
location = / {
  [ configuration A ]
}

location / {
  [ configuration B ]
}

location /documents/ {
  [ configuration C ]
}

location ^~ /images/ {
  [ configuration D ]
}

location ~* \.(gif|jpg|jpeg)$ {
  [ configuration E ]
}
```
则对于如下的请求，它们会分别匹配上面的那个location呢？
- request "/": 会匹配第一个location
- request "/index.html": 会匹配第二个location
- request "/documents/document.html": 会陪陪第三个location
- request "/images/1.gif": 会匹配第四个location
- request "/documents/1.jpg": 则会陪陪最后一个请求


### Setting Up FastCGI Proxying
nginx 可以用来 route requests to FastCGI servers which run applications built with various frameworks and programming languages such as PHP.

要配置 nginx 跟一个 FastCGI 服务器协作，至少要包含如下的指令
- 指令 `fastcgi_pass`: 注意不是设置反向代理的`proxy_pass`指令
- 指令 `fastcgi_param`: 设置要传递给 FastCGI 的参数

下面举例说明，假设 FastCGI server 的地址是 `localhost:9000`, PHP 中， 参数 `SCRIPT_FILENAME` 是用来确定脚本的名字的，
参数 `QUERY_STRING` 是用来传递请求参数的。nginx 可以配置如下：
```nginx
http {
  server {
    location / {
      fastcgi_pass locationhost:9000;
      fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
      fastcgi_param QUERY_STRING    $query_string;
    }

    location ~ \.(gif|jpg|png)$ {
      root /data/images;
    }
  }
}
```
上面的配置会使得nginx 将所有的请求都转发给 FastCGI server, 除了请求静态图像的。


## 汇总
1. Nginx 参考文档：http://nginx.org/en/docs/
2. Nginx Beginner's Guide: http://nginx.org/en/docs/beginners_guide.html
3. Nginx ngx_http_core_module 模块 Core Functionality 的语法说明: http://nginx.org/en/docs/ngx_core_module.html

[0]: http://nginx.org/en/docs/ngx_core_module.html#worker_processes "nginx configuration -- worker processes"
[1]: http://nginx.org/en/docs/http/ngx_http_core_module.html#events "nginx configuration -- events"
[2]: http://nginx.org/en/docs/http/ngx_http_core_module.html#http "nginx configuration -- http"
[3]: http://nginx.org/en/docs/http/ngx_http_core_module.html#server "nginx configuration -- server"
[4]: http://nginx.org/en/docs/http/ngx_http_core_module.html#location "nginx configuration -- location"
[5]: http://nginx.org/en/docs/http/ngx_http_core_module.html#root "nginx configuration -- root"
[6]: http://nginx.org/en/docs/http/ngx_http_core_module.html#proxy_pass "nginx configuration -- proxy pass"


