## Grpc -- Bidirectional Streaming RPC
重磅级的来了，准备好没`\(^o^)/~` 。最后一种即是bidirectional streaming RPC,
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


### protoc 编译生成的client API
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


### Protoc 生成的 Server API
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


### 用户需要实现Server 和 Client 端
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

