> 2016年11月17日 星期四 18时48分47秒 CST

# GO GRPC 学习札记
## :blush: 如何使用

generate codes from .proto file: 

`$ protoc -I IMPORT_DIR PROTO_FILE --go_out=plugins=grpc:EXPORT_DIR`

### [定义一个gRPC][1] 
总共有四种rpc methods 可以定义

* [The Simple RPC][2] 
* [Server-side Streaming RPC][3] 
* [Client-side Streaming RPC][4]
* [Bidirectional Streaming RPC][5]


### 最后的工作
当然在最后，protoc编译.proto文件中生成的go代码还需要将各个rpc方法的处理函数进行注册：
```golang
var _RouteGuide_serviceDesc = grpc.ServiceDesc{
  ServiceName: "routeguide.RouteGuide",
  HandlerType: (*RouteGuideServer)(nil),
  Methods: []grpc.MethodDesc{
    {
      MethodName: "GetFeature",
      Handler:    _RouteGuide_GetFeature_Handler,
    },
  },
  Streams: []grpc.StreamDesc{
    {
      StreamName:    "ListFeatures",
      Handler:       _RouteGuide_ListFeatures_Handler,
      ServerStreams: true,
    },
    {
      StreamName:    "RecordRoute",
      Handler:       _RouteGuide_RecordRoute_Handler,
      ClientStreams: true,
    },
    {
      StreamName:    "RouteChat",
      Handler:       _RouteGuide_RouteChat_Handler,
      ServerStreams: true,
      ClientStreams: true,
    },
  },
  Metadata: "route_guide.proto",
}
```

## gRPC Authentication 
* [gRPC Authentication][6] 

## 汇总
1. 定义gRPC: http://www.grpc.io/docs/tutorials/basic/go.html
2. gRPC Authentication: http://www.grpc.io/docs/guides/auth.html
3. package gRPC: https://godoc.org/google.golang.org/grpc
4. package credentials: https://godoc.org/google.golang.org/grpc/credentials#PerRPCCredentials
5. go中TLS实现,package crypto/tls: https://godoc.org/crypto/tls#Config
6. TLS 协议: https://tools.ietf.org/html/rfc5246

[1]: http://www.grpc.io/docs/tutorials/basic/go.html "gRPC 基础教程--go 语言版"
[2]: method/simple.md
[3]: method/serverstream.md
[4]: method/clientstream.md
[5]: method/bistream.md
[6]: grpc_auth.md

