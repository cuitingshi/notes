# TLS协议学习札记--运行机制篇

TLS 协议是SSL协议的升级版本😁。
TLS协议有两个主要目标
- confidentiality：可以使用symmetric encryption来保证双方的对话没人懂😉，
  TLS经常使用类似于AES这种strong block cipher来对消息进行symmetric encryption,
  不过，以前的流浪器或者平台可能使用Triple DES或者stream cipher RC4来对消息进行加密
- authentication：Authentication is a way to ensure the person on the other end is 
  who they say they are. 使用公钥可以进行authentication。比如说，网站使用证书和公钥
  来想web browsers来证明网站的身份。对于web browsers, 它需要two things to trust a 
  certificate: 
    - proof that the other party is the owner of the certificate:
      对于这个，由于网站的证书中包含有公钥，只要网站证明它拥有对应的私钥，
      则可以向browser证明它确实拥有该证书
    - proof that the certificate is trusted:
      而对于这个，browser认为一个网站的证书可信的充分条件是
      1. 证书必须由受信任的第三方授权发放的
      2. 证书中包含有网站的域名

在web中，TLS通过握手handshake来建立起一个shared key，并证明网站拥有证书

      
## TLS中的handshakes
TLS有两种handshakes,
- 一种是基于RSA算法
- 另外一种是基于Diffie-Hellman算法

上面两种handshakes的区别在于key establishement 和 authentication 是如何建立起来的，
如下表：
|               | Key establishment | Authentication |
| ------------- | ----------------- | -------------- |
| RSA handshake | RSA               | RSA            |
| DH handshake  | DH                | RSA/DSA        |

注意到，对于Authentication:
- RSA handshake只用了一种公钥算法操作，RSA；
- 而DH handshake，如果是RSA证书的话，则同样需要RSA操作，不过Key establishment阶段需要DH操作

此外，考虑如下场景：
给定RSA证书，RSA handshake计算很快， 则
公钥算法（比如RSA和DH）需要耗用CPU很长时间→好吧，这部分是TLS handshake中最耗时的。

DH handshake 虽然需要两种算法，但是这样子可以对key establishment和server的私钥进行解耦合。
这样子的话，即使私钥泄露，消息也不会被解密的😁（即连接具有forward secrecy特性）。
→BTW, DH handshake可以使用non-RSA certificate, 比如ECDSA证书（证书的key是ECDSA类型的），
这个计算性能会相对于RSA来得好的。

### TLS 中的一些关键定义
**1. Session Key**   
handshake会生成session key, 之后会被symmetric cipher用来加密解密client和server间的消息

**2. Client Random**   
client random 是由客户端生成的一个32字节的序列，每次连接都是不一样的。
其组成是4个字节的timestamp + 28 random bytes。而Google Chrome现在使用的32个字节都是随机的，
也被称为`nonce`

**3. Server Random**   
类似于client random, 只不过这个是由server生成的

**4. Pre-master Secret**   
48-byte blob of data。 这个数据可以与client randm, server random作为伪随机函数（pseudorandom function）
的输入，从而生成session key.

**5. Cipher Suite**   
是用来组合TLS连接中的算法的唯一标识符(unique identifier)，对于下面的每个过程都定义了一个算法：
- key establishment (通常是 Diffie-Hellman variant 或者RSA)
- authentication (证书类型)
- confidentiality ( a symmetric cipher)
- integrity (一个哈希函数)

比如，"AES128-SHA"定义了具有如下特性的session:
- RSA for key establishment (implied)
- RSA for authentication (implied)
- 128-bit Advanced Encryption Standard in Cipher Block Chaining mode for confidentiality
- 160-bit Secure Hashing Algorithm (SHA) for integrity

又比如，"ECDHE-ECDSA-AES256-GCM-SHA384"则定义了具有如下特性的session:
- Elliptic Curve Diffie-Hellman Ephemeral (ECDHE) key exchange for key establishment
- Elliptic Curve Digital Signature Algorithms (ECDSA) for authentication
- 256-bit Advanced Standard in Galois/Counter mode (GCM) for confidentiality
- 384-bit Secure Hashing Algorithm for integrity

### RSA Handshake
注意到，握手中双方的消息是不是用session key来加密的，消息是明文发送的😂。
![RSA Handshake 图解](https://blog.cloudflare.com/content/images/2014/Sep/ssl_handshake_rsa.jpg)

具体的Handshake过程如下：
#### 消息1： Client Hello
客户端(web browser)向server端发送Client Hello Message，该消息包含有
- TLS协议版本
- client random
- 客户端所支持的所有cipher suites

现代的browsers可能还会包含如下信息:
- hostname (Server Name Indication, SNI). 

再废话一句，SNI可以使得web server 在同一个IP地址上host 多个域名

#### 消息2： Server Hello
server端接收到消息client hello后，server随机挑选handshake的参数（其实是随机挑一个sipher suite）
消息Server Hello包含了如下信息：
- server random
- server's choson cipher suite
- server's certificate

其中，证书包含了server的公钥和域名（还记得前面说handshake的两个目的吗😁）

#### 消息3：Client Key Exchange
客户端在验证完server发来的证书确实是可信的，并且确实属于客户端要访问的网站之后，
客户端则会生成一个随机的pre-master secret (前面说的48字节的blob)，
然后用证书中的公钥对该数据pre-master secret 进行加密，然后发送给server。


Server端在接收到该消息后，会利用证书中的公钥对应的秘钥对Enc(pre-master secret, public key)进行解密，
得到pre-master secret。

双方都拥有了如下的信息：
- client random
- server random
- pre-master secret

则他们均可以使用上面三个参数以及伪随机函数PRF来生成相同的session key。
这样子的话，下次他们之间要是再发送消息的话，就可以使用session key来进行加密解密了︿(￣︶￣)︿


当client和server交换完消息"Finished"后，则handshake就真正结束了。
再废话一句，其实他们交换的消息是用session key对"client finished"和"server finished"加密的密文。

**最后的思考**   
有没有觉得handshake很神奇，居然把key exchange 和 authentication 结合到一步中：   
因为如果server能够正确得计算出session key的话，那么server必定拥有私钥，   
因此，server必定是证书的所有者

当然，此种版本的handshake也缺点，比如说，当第三方记录下handshake以及之后的communication,
而且，该第三方获取了私钥，则它同样可以解密出premaster secret，然后生成同样的session key,
这样子的话，之后它就可以解密所有的消息了😔

## Ephemeral Diffie-Hellman Handshake

### 准备工作
第二种TLS handshake就是ephemeral Deffie-Hellman handshake了，它主要使用了两种不同的机制：
- 一个是用来建立共享的pre-master secret
- 另外一个是用来authenticate the server

此种handshake最重要的特征是依赖于Diffie-Hellman key agreement algorithm, 下面先简单地说说Diffie-Hellman:

Diffie-Hellman中，双方拥有不同的secrets，他们通过交换消息来获取一个共享的secret。这个版本的handshake主要
依赖于指数可以互相交换，具体来说，对于数字g,有如下公式成立：
<img src="http://chart.googleapis.com/chart?cht=tx&chl=\Large (g^a)^b == (g^b)^a" style="border:none;">

算法的具体流程如下：

- server有 sercret a, 给server发送<img src="http://chart.googleapis.com/chart?cht=tx&chl= g^a" style="border:none;">
- client有 sercret b, 给client发送<img src="http://chart.googleapis.com/chart?cht=tx&chl= g^b" style="border:none;">
- server然后计算出<img src="http://chart.googleapis.com/chart?cht=tx&chl= (g^b)^a" style="border:none;">
- client计算出<img src="http://chart.googleapis.com/chart?cht=tx&chl= (g^a)^b" style="border:none;">
- 这样子的话，双发均拥有<img src="http://chart.googleapis.com/chart?cht=tx&chl= g^{ab}" style="border:none;">，这个值便是他们共享的secret

又因为<img src="http://chart.googleapis.com/chart?cht=tx&chl= g^{ab}" style="border:none;">可能很大，
所以可以取该数字的<img src="http://chart.googleapis.com/chart?cht=tx&chl= n^{th}" style="border:none;"> root作为双方共享的secret.
（比如，使用modular arithmetic，即将该大数除以一个大的质数，然后取相应的余数，之后再在modular arithmetic中取得一个nth root）


Diffie-Hellman key agreement 的另外一个版本是使用Elliptic Curves, ECDHE.

### 进入正题-- Diffie-Hellman Handshake
下面先看一下此种handshake的图解：
![Diffie-hellman Handshake图解](https://blog.cloudflare.com/content/images/2014/Sep/ssl_handshake_diffie_hellman.jpg)



#### 消息1：Client Hello
就像RSA handshake的第一种消息，client hello消息同样包含了如下信息：
- tls 协议版本
- client random
- a list of cipher suites supported
- SNI extension (非必要的)
- the list of curves supported (非必要的，只有在client说要用ECDHE的时候，才会包含这个信息)

#### 消息2： Server Hello
server在接收到client hello消息后，选取好cipher suite以及curve for ECDHE，
会向client发送包含如下信息的Server hello消息：
- server random
- server's chosen cipher suite
- server的证书

上面两个阶段都是跟RSA handshake一样，但是接下来的就不一样了😏。
其实，从server的角度来说，
两者之间的不同在于RSA中premaster-secret是通过证书中的公钥加密、私钥解密获得的，
而DH handshake中，premaster secret是通过交换server DH parameter和client DH parameter
（二者分别对应前面所说的DH算法中的<img src="http://chart.googleapis.com/chart?cht=tx&chl= g^a" style="border:none;">
和<img src="http://chart.googleapis.com/chart?cht=tx&chl= g^b" style="border:none;"> ）
然后, 再结合自身持有的secret a, 从而计算出<img src="http://chart.googleapis.com/chart?cht=tx&chl= (g^b)^a" style="border:none;">,
之后再进行取模等操作计算出共享的secret，即premaster secret.

#### 消息3：Server Key Exchange
首先，这个消息是用于Diffie-Hellman key exchange的（停下来，回忆一下前面简化版的DH算法🤔 ），
因此，server得选取一些starting parameters，发送给客户端（对应前面说的<img src="http://chart.googleapis.com/chart?cht=tx&chl= g^a" style="border:none;">）

又因为前面说过了handshake的一个目的是authenticate the server，因此，
  为了证明server的身份（server的确拥有证书中的公钥对应的私钥），
  server需要利用私钥对于前面的所有消息进行签名, `Sign(hash(messages), private key) --> signature`。

Anyway, Server Key Exchange 消息中包含了如下的信息：
- server DH parameter
- server's signature on all the messages

#### 消息4：Client Key Exchange
client 在接收到server发来的消息3后，会先验证server的证书是可信的，并且证书确实属于client要连接的网站,
然后还得核实server的签名是否有效
- 一方面，利用server之前发来的证书中的公钥解密签名，得到messages的哈希值h1，
- 另外一方面，计算之前的消息的哈希值h2
- 最后，通过对比h1是否等于h2，便可以验证server的签名是否有效，从而验证了server确实拥有相应的私钥。

当然，干完这些验证工作后，需要发送Client Key Exchange消息给server，该消息包含了如下信息：
- client DH parameter


😁，此时，server拥有client DH parameter(对应<img src="http://chart.googleapis.com/chart?cht=tx&chl= g^b" style="border:none;">
)、secret a，
而client拥有Server DH parameter(对应<img src="http://chart.googleapis.com/chart?cht=tx&chl= g^a" style="border:none;">)、secret b，
则二者均可以计算出相同的premaster secrete(对应<img src="http://chart.googleapis.com/chart?cht=tx&chl= g^{ab}" style="border:none;">),
然后，再结合双方均拥有的client random、server random、premaster secret，便可以利用伪随机函数PRF生成相同的session key，
之后，便可以使用sesssion key来加密解密二者之间的消息了✌️

注意，跟前面的RSA handshake相同的是，握手过程的正式结束也是通过互发利用session key
加密后的"client finished"以及"server finished"密文来完成的。


## 附录
### X.509 证书
#### X.509 证书的结构
- Certificate
  - Version Number
  - Serial Number
  - Signature Algorithm ID
  - Issuer Name
  - Validity period
    - Not Before
    - Not After
  - Sbuject name
  - Subject Public Key Info
    - Publick Key Algorithm
    - <font color="red"><b>Subject Public Key</b></font>
  - Issuer Unique Identifier (optional)
  - Subject Unique Identfier (optional)
  - Extensions (optional)
    - ...
  - Certificate Signature Algorithm
  - Certificate Signature

#### 证书的编码及X.509证书中对应的filename extensions
下面是[X.609 标准](https://en.wikipedia.org/wiki/X.690#DER_encoding)中定义的三种编ASN.1编码规则：
1. BER，Basic Encoding Rules
2. CER, Cononical Encoding Rules
3. DER, Distinguished Encoding Rules


下面是X.509证书的文件扩展名字对应的编码格式
- .pem: Privacy-enhanced Electronic Mail， PEM编码格式，其实是在Base64编码的DER证书开头和结尾分别加上"-----BEGIN CERTIFICATE-----"、"-----END CERTIFICATE-----"
- .cer, .crt, .der: 通常是二进制的DER形式
- .p7b, .p7c: PKCS#7,SignedData structure without data, just certificate(s) or CRL(s)
- .p12: PKCS#12, may contain certificate(s)(public) and private keys (password protected)
- .pfx: PFX, PKCS#12的前任，通常包含PKCS#12格式的数据


### 参考资料汇总
1. cloudfare的解说：https://blog.cloudflare.com/keyless-ssl-the-nitty-gritty-technical-details/
2. 当然，要理解TLS协议的运行机制, 还需要了解一下X.509证书的组成以及相关的编码格式（对应证书文件名的后缀）: https://en.wikipedia.org/wiki/X.509
3. 顺便利用openssl工具直观地感受证书的生成以及解码,请参见：https://segmentfault.com/a/1190000002569859
4. 其实还应该了解一下RSA以及DH算法的原理，下次再继续学习了


