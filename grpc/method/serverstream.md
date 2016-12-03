## Grpc -- Server-side Steam 
第二种是server-side是一个stream, 即client只要发送一个request给server，而server返回一个stream, 
client得从stream中读取出一笸箩的messages。定义server-side的rpc的话，
其实只要在response前面加上stream关键字就可以了，比如下面的.proto文件：
```protobuf
// Interface exported by the server.
service RouteGuide {
  //...
  
  // A server-to-client streaming RPC.
  //
  // Obtains the Features available within the given Rectangle.  Results are
  // streamed rather than returned at once (e.g. in a response message with a
  // repeated field), as the rectangle may cover a large area and contain a
  // huge number of features.
  rpc ListFeatures(Rectangle) returns (stream Feature) {}
  
  //...
}
```


protoc编译该.proto文件生成的go源码客户端如下,相比于上面那种simple-rpc,可以注意到客户端如果调用`ListFeatures`方法的话，
返回的会是接口`RouteGuide_ListFeaturesClient`, 用户需要使用该接口的`Recv`方法来接收server端返回的stream Feature。

```golang
type RouteGuideClient interface {
  //...

  // A server-to-client streaming RPC.
  //
  // Obtains the Features available within the given Rectangle.  Results are
  // streamed rather than returned at once (e.g. in a response message with a
  // repeated field), as the rectangle may cover a large area and contain a
  // huge number of features.
  ListFeatures(ctx context.Context, in *Rectangle, opts ...grpc.CallOption) (RouteGuide_ListFeaturesClient, error)

  //...
}


type routeGuideClient struct {
  cc *grpc.ClientConn
}

func (c *routeGuideClient) ListFeatures(ctx context.Context, in *Rectangle, opts ...grpc.CallOption) (RouteGuide_ListFeaturesClient, error) {
  stream, err := grpc.NewClientStream(ctx, &_RouteGuide_serviceDesc.Streams[0], c.cc, "/routeguide.RouteGuide/ListFeatures", opts...)
  if err != nil {
    return nil, err
  }
  x := &routeGuideListFeaturesClient{stream}
  if err := x.ClientStream.SendMsg(in); err != nil {
    return nil, err
  }
  if err := x.ClientStream.CloseSend(); err != nil {
    return nil, err
  }
  return x, nil
}

type RouteGuide_ListFeaturesClient interface {
  Recv() (*Feature, error)
  grpc.ClientStream
}

type routeGuideListFeaturesClient struct {
  grpc.ClientStream
}

func (x *routeGuideListFeaturesClient) Recv() (*Feature, error) {
  m := new(Feature)
  if err := x.ClientStream.RecvMsg(m); err != nil {
    return nil, err
  }
  return m, nil
}
```

protoc编译.proto文件生成的server端所需要的go代码如下，注意到`RouteGuideServer`接口中定义的方法
`ListFeatures(*Rectangle, RouteGuide_ListFeaturesServer) error`，由于是response前边带了关键字stream
（对应server-side streaming RPC)，因此，不同于前边那种simple rpc，传入的第二个参数是一个server stream,
只有Send方法。
```golang
type RouteGuideServer interface {
  // A server-to-client streaming RPC.
  //
  // Obtains the Features available within the given Rectangle.  Results are
  // streamed rather than returned at once (e.g. in a response message with a
  // repeated field), as the rectangle may cover a large area and contain a
  // huge number of features.
  ListFeatures(*Rectangle, RouteGuide_ListFeaturesServer) error
  
  //...
}

func RegisterRouteGuideServer(s *grpc.Server, srv RouteGuideServer) {
  s.RegisterService(&_RouteGuide_serviceDesc, srv)
}

func _RouteGuide_ListFeatures_Handler(srv interface{}, stream grpc.ServerStream) error {
  m := new(Rectangle)
  if err := stream.RecvMsg(m); err != nil {
    return err
  }
  return srv.(RouteGuideServer).ListFeatures(m, &routeGuideListFeaturesServer{stream})
}

type RouteGuide_ListFeaturesServer interface {
  Send(*Feature) error
  grpc.ServerStream
}

type routeGuideListFeaturesServer struct {
  grpc.ServerStream
}

func (x *routeGuideListFeaturesServer) Send(m *Feature) error {
  return x.ServerStream.SendMsg(m)
}
```


所以，作为server的时候，需要实现`RouteGuideServer`接口中定义的方法 `ListFeatures(*Rectangle, RouteGuide_ListFeaturesServer)`，
如下所示。注意到第二个参数传入的是`stream pb.RouteGuide_ListFeaturesServer`,Server发送features的时候是
调用`func (x *routeGuideListFeaturesServer) Send(m *Feature) error`方法，每次只发送一个`Feature`，直至发送完毕，比如下面的实现：

```golang
// ListFeatures lists all features contained within the given bounding Rectangle.
func (s *routeGuideServer) ListFeatures(rect *pb.Rectangle, stream pb.RouteGuide_ListFeaturesServer) error {
  for _, feature := range s.savedFeatures {
    if inRange(feature.Location, rect) {
      if err := stream.Send(feature); err != nil {
        return err
      }
    }
  }
  return nil
}
```


作为client的时候，由于已经实现了`RouteGuideClient`接口，所以只需要简单地调用该接口的实现者`routeGuideClient`中定义的方法即可，
```golang
func (c *routeGuideClient) ListFeatures(ctx context.Context, in *Rectangle, opts ...grpc.CallOption) (RouteGuide_ListFeaturesClient, error)
```

但是由于该方法是server-side streaming RPC，所以返回的是`RouteGuide_ListFeaturesClient`接口，该接口只定义了Recv方法，
所以调用完`ListFeatures`方法之后，客户端需要使用Recv方法读取server端发送的消息流，比如下面的用法：
```golang
// printFeatures lists all the features within the given bounding Rectangle.
func printFeatures(client pb.RouteGuideClient, rect *pb.Rectangle) {
  grpclog.Printf("Looking for features within %v", rect)
  stream, err := client.ListFeatures(context.Background(), rect)
  if err != nil {
    grpclog.Fatalf("%v.ListFeatures(_) = _, %v", client, err)
  }
  for {
    feature, err := stream.Recv()
    if err == io.EOF {
      break
    }
    if err != nil {
      grpclog.Fatalf("%v.ListFeatures(_) = _, %v", client, err)
    }
    grpclog.Println(feature)
  }
}
```

