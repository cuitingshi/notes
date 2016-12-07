## Grpc -- gRPC Authentication
gRPC支持两种[认证机制][1]，一是SSL/TLS, 另外一种是Token-based authentication with Google.
  
### Authentication API

**Credential Type**

有两种类型的credential
- Channel Credentials: 用于Channel认证，比如SSL credentials
- Call Credentials: 用于函数调用认证，比如C++中的ClientContext

其中，对于go语言，[package credentials][2] 
实现了gRPC库所支持的credentials。

### Client端使用SSL/TLS
场景：客户端想授权给server，并且加密所有的数据，则可以如下实现。
首先是C++的实现：
```C++
// create a default SSL ChannelCredentials object
auto creds = grpc::SslCredentials(grpc::SslCredentialsOptions());
// create a channel using the credentials created in the previous step.
auto channel = grpc::CreateChannel(server_name, creds);
// create a stub on the channel
std::unique_ptr<Greeter:Stub> stub(Greeter::NewStub(channel));
// make actual RPC calls on the stub
grpc::Status s = stub->sayHello(&context, *request, response);
```

然后是go语言版本--routeguide客户端
```golang
var (
	tls                = flag.Bool("tls", false, "Connection uses TLS if true, else plain TCP")
	caFile             = flag.String("ca_file", "testdata/ca.pem", "The file containning the CA root cert file")
	serverAddr         = flag.String("server_addr", "127.0.0.1:10000", "The server address in the format of host:port")
	serverHostOverride = flag.String("server_host_override", "x.test.youtube.com", "The server name use to verify the hostname returned by TLS handshake")
)

func main() {
	flag.Parse()
	var opts []grpc.DialOption
	if *tls {
		var sn string
		if *serverHostOverride != "" {
			sn = *serverHostOverride
		}
    // 1. 首先需要定义credentials，有两种方式，一种是用户提供了证书，另外一种是由本进程运行时生成
		var creds credentials.TransportCredentials
		if *caFile != "" {
			var err error
			creds, err = credentials.NewClientTLSFromFile(*caFile, sn)
			if err != nil {
				grpclog.Fatalf("Failed to create TLS credentials %v", err)
			}
		} else {
			creds = credentials.NewClientTLSFromCert(nil, sn)
		}
    // 2. 然后，需要将生成的证书加入到grpc的连接连接可选配置项grpc.DialOption中
		opts = append(opts, grpc.WithTransportCredentials(creds))
	} else {
		opts = append(opts, grpc.WithInsecure())
	}

  // 3. 最后，在连接server的时候加入前面的连接配置项opts
	conn, err := grpc.Dial(*serverAddr, opts...)
	if err != nil {
		grpclog.Fatalf("fail to dial: %v", err)
	}
	defer conn.Close()
	client := pb.NewRouteGuideClient(conn)

	// Looking for a valid feature
	printFeature(client, &pb.Point{Latitude: 409146138, Longitude: -746188906})

	// Feature missing.
	printFeature(client, &pb.Point{Latitude: 0, Longitude: 0})

	// Looking for features between 40, -75 and 42, -73.
	printFeatures(client, &pb.Rectangle{
		Lo: &pb.Point{Latitude: 400000000, Longitude: -750000000},
		Hi: &pb.Point{Latitude: 420000000, Longitude: -730000000},
	})

	// RecordRoute
	runRecordRoute(client)

	// RouteChat
	runRouteChat(client)
}
```

下面是routeguide server端的：
```golang
var (
	tls        = flag.Bool("tls", false, "Connection uses TLS if true, else plain TCP")
	certFile   = flag.String("cert_file", "testdata/server1.pem", "The TLS cert file")
	keyFile    = flag.String("key_file", "testdata/server1.key", "The TLS key file")
	jsonDBFile = flag.String("json_db_file", "testdata/route_guide_db.json", "A json file containing a list of features")
	port       = flag.Int("port", 10000, "The server port")
)

func main() {
	flag.Parse()
	lis, err := net.Listen("tcp", fmt.Sprintf(":%d", *port))
	if err != nil {
		grpclog.Fatalf("failed to listen: %v", err)
	}
	var opts []grpc.ServerOption
	if *tls {
    // 1. 从已有的证书和秘钥中生成credentials
    // 与客户端不同的是，如果需要用TLS的话，credential必须是由现已存在的证书和秘钥来生成的
		creds, err := credentials.NewServerTLSFromFile(*certFile, *keyFile)
		if err != nil {
			grpclog.Fatalf("Failed to generate credentials %v", err)
		}
    // 2. 在grpc.ServerOption中加入证书选项grpc.Creds(creds)
		opts = []grpc.ServerOption{grpc.Creds(creds)}
	}
  // 3. 最后，将选项opts用于创建grpcServer
	grpcServer := grpc.NewServer(opts...)
	pb.RegisterRouteGuideServer(grpcServer, newServer())
	grpcServer.Serve(lis)
}
```

注意，其实在go中credential其实是一个接口
```golang
type TransportCredentials interface {
  // ClientHandshake does the authentication handshake specified by the corresponding
  // authentication protocol on rawConn for clients. It returns the authenticated
  // connection and the corresponding auth information about the connection.
  // Implementations must use the provided context to implement timely cancellation.
  ClientHandshake(context.Context, string, net.Conn) (net.Conn, AuthInfo, error)
    
  // ServerHandshake does the authentication handshake for servers. It returns
  // the authenticated connection and the corresponding auth information about
  // the connection.
  ServerHandshake(net.Conn) (net.Conn, AuthInfo, error)
  
  // Info provides the ProtocolInfo of this TransportCredentials.
  Info() ProtocolInfo

  // Clone makes a copy of this TransportCredentials.
  Clone() TransportCredentials

  // OverrideServerName overrides the server name used to verify the hostname on the returned certificates from the server.
  // gRPC internals also use it to override the virtual hosting name if it is set.
  // It must be called before dialing. Currently, this is only used by grpclb.
  OverrideServerName(string) error
}
```
生成`TransportCredentials`：

对于客户端，`NewClientTLSFromCert`和`NewClientTLSFromFile`均是会返回接口`TransportCredentials`
下面是两个函数的定义：
```golang
func NewClientTLSFromCert(cp *x509.CertPool, serverNameOverride string) TransportCredentials

func NewClientTLSFromFile(certFile, serverNameOverride string) (TransportCredentials, error)
```

对于server端，`NewServerTLSFromCert`和`NewServerTLSFromFile`会返回接口`TransportCredentials`
注意到，server端创建`TransportCredentials`是不同于客户端的，如下：
```golang
// 由server的证书cert构建TransportCredentials
func NewServerTLSFromCert(cert *tls.Certificate) TransportCredentials
// 由存储于磁盘中的证书certFile和秘钥keyFile创建TransportCredentials
func NewServerTLSFromFile(certFile, keyFile string) (TransportCredentials, error)
```

当然，也可以直接通过TLS配置生成`TransportCredentials`，如下
```golang
func NewTLS(c *tls.Config) TransportCredentials
```

要想具体了解TLS,还得去看一下[package crypto/tls][3] 以及 [TLS 协议][4]😁

BTW, 接口`TransportCredentials`已经由tlsCreds实现了,
其重用可以参见hyperledger/fabric/gossip/comm/crypto.go,
下面是grpc/credential对该接口的实现：
```golang
// tlsCreds is the credentials required for authenticating a connection using TLS.
type tlsCreds struct {
    // TLS configuration
    config *tls.Config
}

func (c tlsCreds) Info() ProtocolInfo {
	return ProtocolInfo{
		SecurityProtocol: "tls",
		SecurityVersion:  "1.2",
	}
}

func (c *tlsCreds) ClientHandshake(addr string, rawConn net.Conn, timeout time.Duration) (_ net.Conn, _ AuthInfo, err error) {
	// borrow some code from tls.DialWithDialer
	var errChannel chan error
	if timeout != 0 {
		errChannel = make(chan error, 2)
		time.AfterFunc(timeout, func() {
			errChannel <- timeoutError{}
		})
	}
	// use local cfg to avoid clobbering ServerName if using multiple endpoints
	cfg := *c.config
	if c.config.ServerName == "" {
		colonPos := strings.LastIndex(addr, ":")
		if colonPos == -1 {
			colonPos = len(addr)
		}
		cfg.ServerName = addr[:colonPos]
	}
	conn := tls.Client(rawConn, &cfg)
	if timeout == 0 {
		err = conn.Handshake()
	} else {
		go func() {
			errChannel <- conn.Handshake()
		}()
		err = <-errChannel
	}
	if err != nil {
		rawConn.Close()
		return nil, nil, err
	}
	// TODO(zhaoq): Omit the auth info for client now. It is more for
	// information than anything else.
	return conn, nil, nil
}

func (c *tlsCreds) ServerHandshake(rawConn net.Conn) (net.Conn, AuthInfo, error) {
	conn := tls.Server(rawConn, c.config)
	if err := conn.Handshake(); err != nil {
		rawConn.Close()
		return nil, nil, err
	}
	return conn, TLSInfo{conn.ConnectionState()}, nil
}
```

[1]: http://www.grpc.io/docs/guides/auth.html "GRPC authentication guide"
[2]: https://godoc.org/google.golang.org/grpc/credentials#PerRPCCredentials "gRPC authentication credential"
[3]: https://godoc.org/crypto/tls#Config "go package crypto/tls"
[4]: https://tools.ietf.org/html/rfc5246 "rfc5246 The Transport Layer Security Protocol"
