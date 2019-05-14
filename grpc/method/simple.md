## Grpc -- The Simple RPC
最简单的--client和server端都没有stream，其中客户端使用stub向server发送请求，
  然后等待server返回response。（这个类似于普通的函数调用）
  
  .proto 文件中的定义如下：
   
```protobuf
rpc GetFeature(Point) returns (Feature) {}
message Point {
  int32 latitude = 1;
  int32 longitude = 2;
}
message Feature {
  // The name of the feature.
  string name = 1;

  // The point where the feature is detected.
  Point location = 2;
}
```

  protoc编译该.proto文件生成的go源码中的客户端定义如下：

```go
    
type RouteGuideClient interface {
  // A simple RPC.
  //
  // Obtains the feature at a given position.
  //
  // A feature with an empty name is returned if there's no feature at the given
  // position.
  GetFeature(ctx context.Context, in *Point, opts ...grpc.CallOption) (*Feature, error)
  //....
}

type routeGuideClient struct {
  cc *grpc.ClientConn
}

func NewRouteGuideClient(cc *grpc.ClientConn) RouteGuideClient {
  return &routeGuideClient{cc}
}

func (c *routeGuideClient) GetFeature(ctx context.Context, in *Point, opts ...grpc.CallOption) (*Feature, error) {
  out := new(Feature)
  err := grpc.Invoke(ctx, "/routeguide.RouteGuide/GetFeature", in, out, c.cc, opts...)
  if err != nil {
    return nil, err
  }
  return out, nil
}
```

  protoc编译该.proto文件生成的go源码中的server短定义如下：
```go
type RouteGuideServer interface {
  // A simple RPC.
  //
  // Obtains the feature at a given position.
  //
  // A feature with an empty name is returned if there's no feature at the given
  // position.
  GetFeature(context.Context, *Point) (*Feature, error)
  //...
}

func RegisterRouteGuideServer(s *grpc.Server, srv RouteGuideServer) {
  s.RegisterService(&_RouteGuide_serviceDesc, srv)
}

func _RouteGuide_GetFeature_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
  in := new(Point)
  if err := dec(in); err != nil {
    return nil, err
  }
  if interceptor == nil {
    return srv.(RouteGuideServer).GetFeature(ctx, in)
  }
  info := &grpc.UnaryServerInfo{
    Server:     srv,
    FullMethod: "/routeguide.RouteGuide/GetFeature",
  }
  handler := func(ctx context.Context, req interface{}) (interface{}, error) {
    return srv.(RouteGuideServer).GetFeature(ctx, req.(*Point))
  }
  return interceptor(ctx, in, info, handler)
}
```
    
  所以，作为server的时候，需要实现`RouteGuideServer`接口中定义的`GetFeature`方法，
```go
type routeGuideServer struct {
  savedFeatures []*pb.Feature
  routeNotes    map[string][]*pb.RouteNote
}

// GetFeature returns the feature at the given point.
func (s *routeGuideServer) GetFeature(ctx context.Context, point *pb.Point) (*pb.Feature, error) {
  for _, feature := range s.savedFeatures {
    if proto.Equal(feature.Location, point) {
      return feature, nil
    }
  }
  // No feature was found, return an unnamed feature
  return &pb.Feature{Location: point}, nil
}
```

  而作为客户端，其实，只是单纯地调用编译器protoc中已经实现的`RouteGuideClient`接口，
  即方法`func (c *routeGuideClient) GetFeature(...)`,比如如下的客户端的使用，
```go
// printFeature gets the feature for the given point.
func printFeature(client pb.RouteGuideClient, point *pb.Point) {
  grpclog.Printf("Getting feature for point (%d, %d)", point.Latitude, point.Longitude)
  feature, err := client.GetFeature(context.Background(), point)
  if err != nil {
    grpclog.Fatalf("%v.GetFeatures(_) = _, %v: ", client, err)
  }
  grpclog.Println(feature)
}
```

