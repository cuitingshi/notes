>2016年12月 8日 星期四 17时42分07秒 CST

# Nginx 作为 HTTP Load Balancer
对不同的应用程序实例进行负载均衡化是互联网中比较常用的一个技术，利用负载均衡可以优化资源的利用率、最大化吞吐率、
减少延迟时间、还能够保证 fault-tolerant configurations.

而 nginx 可以配置为高效的 HTTP 负载均衡器, 实现如下的功能：

1. distribute traffic to several application servers 
2. improve permance, scalability and reliability of web applications

## Load Balancing Methods
nginx 支持如下的 load balancing mechanisms (or methods):
  - round-robin: 目的为应用程序服务器的请求会按照 round-robin 的方式分发给各个server
  - least-connected: 即将请求分配给活跃连接数最少的server
  - ip-hash: 使用Hash(client_ip_address) 来决定下个请求会转发给哪个server


## Default Load Balancing Configuration
用 nginx 做负载均衡的最简单的配置如下：
```nginx
http {
  upstream myapp1 {
    server srv1.example.com;
    server srv2.example.com;
    server srv3.example.com;
  }

  server {
    listen 80;

    location / {
      proxy_pass http://myapp1;
    }
  }
}
```
上面的配置中，同一个应用程序myapp1 有三个实例，分别运行在 srv1-srv3. 
当配置中没有指定负载均衡方法的时候，默认使用round-robin. 所有的请求都会被代理到 server group myapp1,
同时，nginx applies HTTP load balancing to distribute the requests.

Reverse proxy implementation in nginx include load balancing for HTTP, HTTPS, FastCGI, uwsgi, SCGI, and memcached.

- 如果要为HTTPS而不是HTTP配置负载均衡的话，只要在协议中使用`https`就可以了😁;
- 不过，如果是为 FastCGI, uwsgi, SCGI 或者 memcached 设置负载均衡的话，需要分别使用指令`fastcgi_pass, uwsgi_pass, scgi_pass, memcached_pass`

### Least Connected Load Balancing
如果配置了 Least-connected 负载均衡策略， nginx 会尽可能将新的请求转发给 a less busy server, 而不是 overload a busy application with excessive requests.

在`upstream` 指令里面使用指令`least_conn;`便可以指定nginx的负载均衡策略为least connected load balancing, 如下：
```nginx
http {
  upstream myapp1 {
    least_conn;
    server srv1.example.com;
    server srv2.example.com;
    server srv3.example.com;
  }
}
```

### Session Persistence
注意，上面两种负载均衡策略（round-bin、least-connected load balancing），each subsequent client's request 可能会转发给不同的server. 
并不能保证同一个客户的请求总是会分发给同一个server.😳

因此，如果需要将同一个客户绑定到特定一个应用程序服务器，即 make the client's session "sticky" or "persistent" (每次都会选择同一个server), 
就可以采用 ip-hash load balancing mechanism.

采用 ip-hash 负载均衡策略时，nginx 会通过 hash(client_ip_address) 来决定选择 server group 中的那个 server 来处理客户的请求。

在`upstream` 指令中加入指令`ip_hash;` 便可以指定nginx 的负载均衡策略为 ip_hash load balancing. 
```nginx
http {
  upstream myapp1 {
    ip_hash;
    server srv1.example.com;
    server srv2.example.com;
    server srv3.example.com;
  }
}
```

### Weighted Load Balancing
好吧，其实还有通过指定 server 的权重参数 `weight` 来影响 nginx 的负载均衡算法。

在 round-robin 负载均衡策略中可以按如下的方式配置使用 `weight` 参数：
```nginx
http {
  upstream myapp1 {
    server srv1.example.com weight=3;
    server srv2.example.com;
    server srv3.example.com;
  }
}
```
如果配置如上的话，则每五个新的请求的转发情况为：
- 3 个请求转发给 srv1
- 1 个请求转发给 srv2
- 1 个请求转发给 srv3

当然，最新版本的nginx中 least-connected 和 ip-hash load balancing 中也可以使用 `weight`参数。


注意，除了上面提到的指令来配置nginx中的负载均衡，还有其他指令或者参数影响负载均衡策略：

1. 指令 [proxy_next_upstream][1], 
2. `server` 指令参数
  - [backup][2], 该参数是类似于weight, 属于`server address [parameters]` 中的参数，`backup`参数表明该server 是作为冗余的备份server的，
  当且仅当那些主要的servers不可以的时候，请求才会转发给该备份server
  - [down][2], 是`server address [parameters]` 中的一个参数， 标记该server为永久不可用
3. 指令 [keepalive][3]: 语法形式是` keepalive connections;`, 嵌套在 context `upstream` 中使用，该指令表示为connections to upstream servers 激活缓存。
  其中参数`connetions` sets the maximum number of idle keepalive connections to upstream servers that are preserved in the cache of each worker process.
  当超过最大连接数时，最近最少使用的连接将会被关闭

  下面举例来说明keepalive 指令的用法：
首先来看看如何配置一个 memecached upstream with keepalive connections
```nginx
upstream memcached_backend {
  server 127.0.0.1:11211;
  server 10.0.0.2:11211;

  keepalive 32;
}
server {
  ...
  
  location /memcached/ {
    set $memcached_key $uri;
    memcached_pass memcached_backend;
  }
}
```
 
然后再看看 HTTP upstream 的配置， 不过得注意指令`proxy_http_version` 应该设置成"1.1", 指令`proxy_set_header` 中的 `Connection` header field 应该清空
```nginx
upstream http_backentd {
  server 127.0.0.1:8080;

  keepalive 16;
}

server {
  ...

  location /http/ {
    proxy_pass http://http_backend;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    ...
  }
}
```

最后再看看 FastCGI servers, 这个需要设置指令`fastcgi_keep_conn on;` 来保证 keepalive 连接能够运作：
```nginx
upstream fastcgi_backend {
  server 127.0.0.1:9000;

  keepalive 8;
}

server {
  ...

  location /fastcgi/ {
    fastcgi_pass fastcgi_backend;
    fastcgi_keep_conn on;
  }
}
```



[1]: http://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_next_upstream "nginx load balancing configuration -- proxy_next_upstream"
[2]: http://nginx.org/en/docs/http/ngx_http_upstream_module.html#server "nginx load balancing configuration -- backup, down"
[3]: http://nginx.org/en/docs/http/ngx_http_upstream_module.html#keepalive "nginx load balancing configuration -- keepalive"
