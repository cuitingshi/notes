# GO GRPC 学习札记

> 2016年11月17日 星期四 18时48分47秒 CST


## 如何使用
generate codes from .proto file: 

`$ protoc -I IMPORT_DIR PROTO_FILE --go_out=plugins=grpc:EXPORT_DIR`

### [定义一个gRPC](http://www.grpc.io/docs/tutorials/basic/go.html)
总共有四种rpc methods 可以定义
1. 最简单的--client和server端都没有stream，其中客户端使用stub向server发送请求，
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
    ```golang
        
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
    ```golang
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
    ```golang
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
    ```golang
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
    


2. 第二种是server-side是一个stream, 即client只要发送一个request给server，
    而server返回一个stream, client得从stream中读取出一笸箩的messages。定义server-side的rpc的话，
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

    protoc编译该.proto文件生成的go源码客户端如下,相比于上面那种simple-rpc,可以注意到
    客户端如果调用`ListFeatures`方法的话，返回的会是接口`RouteGuide_ListFeaturesClient`,
    用户需要使用该接口的`Recv`方法来接收server端返回的stream Feature。
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

    所以，作为server的时候，需要实现`RouteGuideServer`接口中定义的方法
    `ListFeatures(*Rectangle, RouteGuide_ListFeaturesServer)`，比如：
    注意到第二个参数传入的是`stream pb.RouteGuide_ListFeaturesServer`,Server发送features的时候是
    调用`func (x *routeGuideListFeaturesServer) Send(m *Feature) error`方法，每次只发送一个`Feature`，
    直至发送完毕，比如下面的实现：

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

3. 第三种是client-side streaming RPC，其中客户端写一笸箩的消息发送给server，
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

4. 重磅级的来了，准备好没`\(^o^)/~` 。最后一种即是bidirectional streaming RPC,
    其中client端和server端均使用read-write stream。两个stream是独立运作互不影响的，
    所以client端和server端想咋读咋写都可以的😏：比如说，
    
    - server端可以等接收完所有的client端发送来的消息后再写response到stream中；
    - 或者可以收到一条client端发送来的消息就写一条message给client端；
    - 或者其它组合

    类似于前面两种方法，只要在request和response类型前面加上关键字stream，
    就可以定义一个bidirectional streaming RPC,如下的.proto定义：
    ```protobuf
    service RouteGuide {   
      // A Bidirectional streaming RPC.
      //
      // Accepts a stream of RouteNotes sent while a route is being traversed,
      // while receiving other RouteNotes (e.g. from other users).
      rpc RouteChat(stream RouteNote) returns (stream RouteNote) {}
    }

    // A RouteNote is a message sent while at a given point.
    message RouteNote {
      // The location from which the message is sent.
      Point location = 1;

      // The message to be sent.
      string messge = 2;
    }
    ```

    protoc编译生成的客户端go代码如下所示，其中，如果客户端在调用完RouteChat方法后，
    会返回接口`RouteGuide_RouteChatClient`,
    
    - 然后如果需要发送消息的话，则需要调用该接口中定义的`Send(m *RouteNote)`方法
    - 如果需要接收消息的话，则需要调用该接口中定义的`Recv()(*RouteNote,, error)`方法
    
    具体的代码如下：
    ```golang
    type RouteGuideClient interface {
      // ...

      // A Bidirectional streaming RPC.
      //
      // Accepts a stream of RouteNotes sent while a route is being traversed,
      // while receiving other RouteNotes (e.g. from other users).
      RouteChat(ctx context.Context, opts ...grpc.CallOption) (RouteGuide_RouteChatClient, error)
    }

    func (c *routeGuideClient) RouteChat(ctx context.Context, opts ...grpc.CallOption) (RouteGuide_RouteChatClient, error) {
      stream, err := grpc.NewClientStream(ctx, &_RouteGuide_serviceDesc.Streams[2], c.cc, "/routeguide.RouteGuide/RouteChat", opts...)
      if err != nil {
        return nil, err
      }
      x := &routeGuideRouteChatClient{stream}
      return x, nil
    }

    type RouteGuide_RouteChatClient interface {
      Send(*RouteNote) error
      Recv() (*RouteNote, error)
      grpc.ClientStream
    }

    type routeGuideRouteChatClient struct {
      grpc.ClientStream
    }

    func (x *routeGuideRouteChatClient) Send(m *RouteNote) error {
      return x.ClientStream.SendMsg(m)
    }

    func (x *routeGuideRouteChatClient) Recv() (*RouteNote, error) {
      m := new(RouteNote)
      if err := x.ClientStream.RecvMsg(m); err != nil {
        return nil, err
      }
      return m, nil
    }
    ```

    protoc编译.proto文件生成的server API如下所示，其中，server端需要实现接口RouteGuideServer，
    在实现的时候，可以调用接口`RouteGuide_RouteChatServer`中定义的方法`Send(*RouteNote) error`
    来发送消息给客户端，使用方法`Recv()(*RouteNote, error)`可以接受客户端发送的消息:
    ```golang
    type RouteGuideServer interface {
      // A Bidirectional streaming RPC.
      //
      // Accepts a stream of RouteNotes sent while a route is being traversed,
      // while receiving other RouteNotes (e.g. from other users).
      RouteChat(RouteGuide_RouteChatServer) error
    }

    func _RouteGuide_RouteChat_Handler(srv interface{}, stream grpc.ServerStream) error {
      return srv.(RouteGuideServer).RouteChat(&routeGuideRouteChatServer{stream})
    }

    type RouteGuide_RouteChatServer interface {
      Send(*RouteNote) error
      Recv() (*RouteNote, error)
      grpc.ServerStream
    }

    type routeGuideRouteChatServer struct {
      grpc.ServerStream
    }

    func (x *routeGuideRouteChatServer) Send(m *RouteNote) error {
      return x.ServerStream.SendMsg(m)
    }

    func (x *routeGuideRouteChatServer) Recv() (*RouteNote, error) {
      m := new(RouteNote)
      if err := x.ServerStream.RecvMsg(m); err != nil {
        return nil, err
      }
      return m, nil
    }
    ```

    因此，对于server端，可以按照如下来实现上面编译生成的server API,
    ```golang

    // RouteChat receives a stream of message/location pairs, and responds with a stream of all
    // previous messages at each of those locations.
    func (s *routeGuideServer) RouteChat(stream pb.RouteGuide_RouteChatServer) error {
      for {
        in, err := stream.Recv()
        if err == io.EOF {
          return nil
        }
        if err != nil {
          return err
        }
        key := serialize(in.Location)
        if _, present := s.routeNotes[key]; !present {
          s.routeNotes[key] = []*pb.RouteNote{in}
        } else {
          s.routeNotes[key] = append(s.routeNotes[key], in)
        }
        for _, note := range s.routeNotes[key] {
          if err := stream.Send(note); err != nil {
            return err
          }
        }
      }
    }
    ```

    对于客户端，可以像下面这样子使用，使用一个goroutine来接收server端发送来的消息，注意到
    当server端不再有消息发送来的时候（`err == io.EOF`），则通过关闭信道`waitc`来通知main goroutine
    来结束：
    ```golang
    // runRouteChat receives a sequence of route notes, while sending notes for various locations.
    func runRouteChat(client pb.RouteGuideClient) {
      notes := []*pb.RouteNote{
        {&pb.Point{Latitude: 0, Longitude: 1}, "First message"},
        {&pb.Point{Latitude: 0, Longitude: 2}, "Second message"},
        {&pb.Point{Latitude: 0, Longitude: 3}, "Third message"},
        {&pb.Point{Latitude: 0, Longitude: 1}, "Fourth message"},
        {&pb.Point{Latitude: 0, Longitude: 2}, "Fifth message"},
        {&pb.Point{Latitude: 0, Longitude: 3}, "Sixth message"},
      }
      stream, err := client.RouteChat(context.Background())
      if err != nil {
        grpclog.Fatalf("%v.RouteChat(_) = _, %v", client, err)
      }
      waitc := make(chan struct{})
      go func() {
        for {
          in, err := stream.Recv()
          if err == io.EOF {
            // read done.
            close(waitc)
            return
          }
          if err != nil {
            grpclog.Fatalf("Failed to receive a note : %v", err)
          }
          grpclog.Printf("Got message %s at point(%d, %d)", in.Message, in.Location.Latitude, in.Location.Longitude)
        }
      }()
      for _, note := range notes {
        if err := stream.Send(note); err != nil {
          grpclog.Fatalf("Failed to send a note: %v", err)
        }
      }
      stream.CloseSend()
      <-waitc
    }
    ```

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

## gRPC [Authentication](http://www.grpc.io/docs/guides/auth.html)
    gRPC支持两种认证机制，一是SSL/TLS, 另外一种是Token-based authentication with Google.
  
### Authentication API

**Credential Type**

有两种类型的credential
- Channel Credentials: 用于Channel认证，比如SSL credentials
- Call Credentials: 用于函数调用认证，比如C++中的ClientContext

其中，对于go语言，[package credentials](https://godoc.org/google.golang.org/grpc/credentials#PerRPCCredentials)
实现了gRPC库所支持的credentials。

#### Client端使用SSL/TLS
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

要想具体了解TLS,还得去看一下[package crypto/tls](https://godoc.org/crypto/tls#Config)
以及[TLS 协议](https://tools.ietf.org/html/rfc5246)😁

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

## 汇总
1. 定义gRPC: http://www.grpc.io/docs/tutorials/basic/go.html
2. gRPC Authentication: http://www.grpc.io/docs/guides/auth.html
3. package gRPC: https://godoc.org/google.golang.org/grpc
4. package credentials: https://godoc.org/google.golang.org/grpc/credentials#PerRPCCredentials
5. go中TLS实现,package crypto/tls: https://godoc.org/crypto/tls#Config
6. TLS 协议: https://tools.ietf.org/html/rfc5246
