## Grpc -- Client-side Straming RPC
第三种是client-side streaming RPC，其中客户端写一笸箩的消息发送给server，
当客户端发送完所有的消息后，客户端需要等待server端读取完所有的消息，然后
返回server端的response。通过在request类型的前面加上关键字stream，即可以
定义一个client-side streaming RPC，如下：
```protobuf
service RouteGuide {
  
  // A client-to-server streaming RPC.
  //
  // Accepts a stream of Points on a route being traversed, returning a
  // RouteSummary when traversal is completed.
  rpc RecordRoute(stream Point) returns (RouteSummary) {}

  //...
}

message RouteSummary {
  // The number of points received.
  int32 point_count = 1;

  // The number of known features passed while traversing the route.
  int32 feature_count = 2;

  // The distance covered in metres.
  int32 distance = 3;

  // The duration of the traversal in seconds.
  int32 elapsed_time = 4;
}
```


protoc编译该.proto文件生成的go源码客户端如下,相比于第一种simple-rpc,可以注意到
客户端如果调用`RecordRoute`方法的话，返回的会是接口`RouteGuide_RecordRouteClient`,
用户需要使用该接口的`Send`方法来给server端发送那笸箩的messages（Point类型），
然后使用`CloseAndRecv()(*RouteSummary, error)`方法来进行接收server最后的response：
```golang
type RouteGuideClient interface {
  // A client-to-server streaming RPC.
  //
  // Accepts a stream of Points on a route being traversed, returning a
  // RouteSummary when traversal is completed.
  RecordRoute(ctx context.Context, opts ...grpc.CallOption) (RouteGuide_RecordRouteClient, error)
  //...
}

type routeGuideClient struct {
  cc *grpc.ClientConn
}

func NewRouteGuideClient(cc *grpc.ClientConn) RouteGuideClient {
  return &routeGuideClient{cc}
}

func (c *routeGuideClient) RecordRoute(ctx context.Context, opts ...grpc.CallOption) (RouteGuide_RecordRouteClient, error) {
  stream, err := grpc.NewClientStream(ctx, &_RouteGuide_serviceDesc.Streams[1], c.cc, "/routeguide.RouteGuide/RecordRoute", opts...)
  if err != nil {
    return nil, err
  }
  x := &routeGuideRecordRouteClient{stream}
  return x, nil
}

type RouteGuide_RecordRouteClient interface {
  Send(*Point) error
  CloseAndRecv() (*RouteSummary, error)
  grpc.ClientStream
}

type routeGuideRecordRouteClient struct {
  grpc.ClientStream
}

func (x *routeGuideRecordRouteClient) Send(m *Point) error {
  return x.ClientStream.SendMsg(m)
}

func (x *routeGuideRecordRouteClient) CloseAndRecv() (*RouteSummary, error) {
  if err := x.ClientStream.CloseSend(); err != nil {
    return nil, err
  }
  m := new(RouteSummary)
  if err := x.ClientStream.RecvMsg(m); err != nil {
    return nil, err
  }
  return m, nil
}
```


protoc编译.proto文件生成的server端所需要的go代码如下，注意到`RouteGuideServer`接口中定义的方法
`RecordRoute(RouteGuide_RecordRouteServer) error`，由于是request类型前边带了关键字stream
（对应client-side streaming RPC)，因此，不同于前边那种simple rpc，传入的参数是`RouteGuide_RecordRouteServer`接口，
有`Recv()(*Point, error)`和`SendAndClose(*RouteSummary) error`方法:
```golang
type RouteGuideServer interface {
  // A client-to-server streaming RPC.
  //
  // Accepts a stream of Points on a route being traversed, returning a
  // RouteSummary when traversal is completed.
  RecordRoute(RouteGuide_RecordRouteServer) error
  //...
}

func _RouteGuide_RecordRoute_Handler(srv interface{}, stream grpc.ServerStream) error {
  return srv.(RouteGuideServer).RecordRoute(&routeGuideRecordRouteServer{stream})
}

type RouteGuide_RecordRouteServer interface {
  SendAndClose(*RouteSummary) error
  Recv() (*Point, error)
  grpc.ServerStream
}

type routeGuideRecordRouteServer struct {
  grpc.ServerStream
}

func (x *routeGuideRecordRouteServer) SendAndClose(m *RouteSummary) error {
  return x.ServerStream.SendMsg(m)
}

func (x *routeGuideRecordRouteServer) Recv() (*Point, error) {
  m := new(Point)
  if err := x.ServerStream.RecvMsg(m); err != nil {
    return nil, err
  }
  return m, nil
}
```


因此，对于server端的话，需要实现RecordRoute方法,需要在for循环中
使用接口`pb.RouteGuide_RecordRouteServer`中定义的Recv方法，
当接收完毕的时候（err == io.EOF），则需要调用`SendAndClose(m *RouteSummary)`方法来向client端发送
最终的Response，
```golang
// RecordRoute records a route composited of a sequence of points.
//
// It gets a stream of points, and responds with statistics about the "trip":
// number of points,  number of known features visited, total distance traveled, and
// total time spent.
func (s *routeGuideServer) RecordRoute(stream pb.RouteGuide_RecordRouteServer) error {
  var pointCount, featureCount, distance int32
  var lastPoint *pb.Point
  startTime := time.Now()
  for {
    point, err := stream.Recv()
    if err == io.EOF {
      endTime := time.Now()
      return stream.SendAndClose(&pb.RouteSummary{
        PointCount:   pointCount,
        FeatureCount: featureCount,
        Distance:     distance,
        ElapsedTime:  int32(endTime.Sub(startTime).Seconds()),
      })
    }
    if err != nil {
      return err
    }
    pointCount++
    for _, feature := range s.savedFeatures {
      if proto.Equal(feature.Location, point) {
        featureCount++
      }
    }
    if lastPoint != nil {
      distance += calcDistance(lastPoint, point)
    }
    lastPoint = point
  }
}
```


而对于client端，在调用完统一的RPC方法后
` RecordRoute(ctx context.Context, opts ...grpc.CallOption) (RouteGuide_RecordRouteClient, error)`，
需要使用接口`RouteGuide_RecordRouteClient`中定义的方法Send来向Server端发送消息(一笸箩的Points),
比如下面的用法：
```golang
// runRecordRoute sends a sequence of points to server and expects to get a RouteSummary from server.
func runRecordRoute(client pb.RouteGuideClient) {
  // Create a random number of random points
  r := rand.New(rand.NewSource(time.Now().UnixNano()))
  pointCount := int(r.Int31n(100)) + 2 // Traverse at least two points
  var points []*pb.Point
  for i := 0; i < pointCount; i++ {
    points = append(points, randomPoint(r))
  }
  grpclog.Printf("Traversing %d points.", len(points))
  stream, err := client.RecordRoute(context.Background())
  if err != nil {
    grpclog.Fatalf("%v.RecordRoute(_) = _, %v", client, err)
  }
  for _, point := range points {
    if err := stream.Send(point); err != nil {
      grpclog.Fatalf("%v.Send(%v) = %v", stream, point, err)
    }
  }
  reply, err := stream.CloseAndRecv()
  if err != nil {
    grpclog.Fatalf("%v.CloseAndRecv() got error %v, want %v", stream, err, nil)
  }
  grpclog.Printf("Route summary: %v", reply)
}
```

