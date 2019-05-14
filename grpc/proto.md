# google protobuf 学习札记

## [protocol buffers][1]
其实google 的protobuf作用有两个：
1. 通过.proto文件来定义数据结构（它的message类型相当于struct），

2. 然后通过其自带的编译器来生成将该数据结构序列化和反序列化的特定语言（c++, go, java, rugby...）
  的数据结构和方法，然后再通过特定语言下的proto包/库来进行序列化、反序列化方法

## [go中使用protobuf][1] 
### 定义数据结构.proto
  proto文件开头指定所编译生成的go文件的package的声明，
  ```protobuf
  syntax = "proto3";
  package tutorial;
  ```

**Message**

Definitions: A message is just an aggregate containing a set of typed fields. 

其中，field的类型可以为string, int32, bool, float, double, 也可以为自定义的message的类型
（相当于message后面跟的就是新的类型，比如下面的Person, PhoneNumber, AddressBook都是可以
嵌套作为其他人的类型的）当然，也可以自定义类型，

```protobuf
message Person {
  string name = 1;
  int32 id = 2; 
  string email = 3;

  enum PhoneType {
    MOBILE = 0;
    HOME = 1;
    WORK = 2;
  }
  message PhoneNumber {
    string number = 1;
    PhoneType type = 2;
  }
  repeated PhoneNumber phones = 4;
}

message AddressBook {
  repeated Person peaple = 1;
}
```

### 编译运行
1. 首先保证你得安装了编译器protoc以及Go protocol buffers 插件，
  插件可以直接用go命令获取：`$ go get -u github.com/go/protobuf/protoc-gen-go`

2. 利用如下命令编译proto文件生成go文件：
  `$ protoc -I=$SRC_DIR --go_out=$DST_DIR $SRC_DIR/*.proto`,
    其中，-I命令指定了你所要编译的proto文件所在的目录，
    而--go_out既表明了你要生成的代码的类型是go语言，同时
    表明了proto文件编译生成的代码要放在$DST-DIR这个文件夹下
    PS: 每个proto编译生成的文件名字为\*.pb.go. 

### The Protocol Buffer API
利用protoc 编译生成addressbook.pb.go的时候回生成如下类型：
- An `AddressBook` structure with a `People` field
- A `Person` structure with fields for `Name, Id, Email, Phones`
- A `Person_PhoneNumber` structure, with fields for `Number, Type`
- The type `Person_PhoneTpe` and a value defined for each value in the `Person.PhoneType` enum.

比如说，使用protoc编译生成的go文件中的Person类型生成一个变量，
```go
p := pb.Person{
  Id: 1234,
  Name: "John Doe",
  Email: "doeJ@xyz.com",
  Phones: []*pb.Person-PhoneNumber{
    {Number: "234234", Type: pb.Person_HOME},
  },
}
```
### 序列化和反序列化
有了由proto定义转化而来的数据结构（go语言的），则可以采用`proto` library的`Marshal(pb.Message)([]byte, error)`
来进行序列化，利用`Unmarshal([]byte, pb.Message)error`来进行反序列化了。


## [proto的语法][2] 
### Message 类型中Field Rules
  - sigular: 直接使用scalar value type 或者 enum, message类型
  - `repeated`: 比如下面的`repeated string snippets = 1;`, `repeated`关键字放在
    类型的前面，表示这个field可以重复任意次数，在proto3中`repeated` fileds of 
    scalar numeric types use `packed` encoding by default

### Message 类型中的Reserved fields
感觉用处很大😁，其实就是改变了某个message的成员变量（删除了或者注释掉了某个field）,
则可以通过关键字`researved <tag_number | field_name>`来保留着该成员变量的tag number,这样就可以
做到兼容旧版本的message类型😋：
```protobuf
message Foo {
  reserved 2, 15, 9 to 11;
  reserved "foo", "bar";
}
```

### Message 类型

**Scalar Value Type**

| .proto Type | Go Type |
|:--- |:---:|
| double | float64 |
| float | float32 |
| int32 | int32 |
| int64 | int64 |
| uint32 | uint32 |
| uint64 | uint64 |
| bool | bool |
| string | string |
| bytes | []byte |


**Composite Type**

*1. Enumberation*

可以通过enum关键字定义枚举类型, 比如下面的类型`Corpus`，这个就是枚举类型，
```protobuf
message SearchRequest {
  string query = 1;
  int32 page_number = 2;
  int32 result_per_page = 3;
  enum Corpus {
    UNIVERSAL = 0;
    WEB = 1;
    IMAGES = 2;
    LOCAL = 3;
    NEWS = 4;
    PRODUCTS = 5;
    VIDEO = 6;
  }
  Corpus corpus = 4;
}
```
其中，定义了复合类型SearchRequest, 该类型中由4个成员变量，即`query, page_number,
  result_per_page, corpus`, 注意，该类型内部还定义了一个枚举类型Corpus，两个类型对应的编译
  生成的go的类型分别是`pb.SearchRequest`和`pb.SearchRequest_Corpus`


*2. Message*

当然也可以使用复合类型message

- 对于同一个proto文件中的message类型，可以直接引用：
  ```protobuf
    message SearchResponse {
      repeated Result results = 1;
    }

    message Result {
      string url = 1;
      string title = 2;
      repeated string snippets = 3;
    }
  ```

- 对于另外一个proto文件中定义的message类型，可以通过`import`关键字引进
  ```protobuf
    import "myproject/other_protos.proto";
  ```

PS: 另外一个qiyingyiqiao, ^0^, 
  如果把proto文件移到其它目录下了，则可以在原本的目录下，创建一个同样
  名字的proto文件，然后利用`import public`关键字来引入，
  ```protobuf
  // new.proto
  // 所有的旧proto文件中的定义均移到了new.proto文件中
  ```
  则为了保持项目的不变性，则可以在原本的proto文件中写入
  ```protobuf
  // old.proto
  // 其它的proto文件都是引用old.proto的
  import public "new.proto";
  import "other.proto";
  ```
  这样子的话，其它引用old.proto文件的保持原样就可以了，不用改😄，
  ```protobuf
  // client.proto
  import "old.proto";
  // 这里可以使用old.proto和new.proto文件中的定义的message类型，但是
  // 不可以使用other.proto中定义的message类型
  ```

  
### Any 消息类型
在没有引用某种类型的.proto的定义的时候，使用`Any`类型便可以把messages当成
嵌入类型来用。一个`Any`类型的变量是由任意已序列化的消息类型（其实是`bytes`类型😭)
以及一个URL字符串组成的。
`Any`类型的定义如下：
```protobuf
string type_url = 1;
bytes value = 2;
```

如果要使用`Any`类型的话，需要：
```protobuf
import "google/protobuf/any.proto";

message ErrorStatus {
  string message = 1;
  repeated google.protobuf.Any details = 2;
}
```

其中，The default type URL for a given message type is `type.googleapis.com/packagename.messagename.`


### Oneof 关键字（类型修饰符）
其实这个类型有点像C中的Union类型，多个变量共享一段内存（∵每次只有一个变量存进去丫😂），
所以说如果想要节省内存空间（其实这里不应该用内存，因为这里想要表明的是对类型序列化后的
所需要的存储空间😏）。在.proto文件中定义Oneof，
```protobuf
message Column {
	oneof value {
    string string = 1;
    int32 int32 = 2;
		int64 int64 = 3;
		uint32 uint32 = 4;
		uint64 uint64 = 5;
		bytes bytes = 6;
		bool bool = 7;
  }
}

```
注意，oneof里面的成员变量fields的类型不可以有`repeated`关键字;
还有，对于oneof变量进行赋值的话，会删掉原本的值。

上面的Column类型编译后生成的代码是，注意其中oneof是用接口类型实现的,
```go
type Column struct {
	// Types that are valid to be assigned to Value:
	//	*Column_String_
	//	*Column_Int32
	//	*Column_Int64
	//	*Column_Uint32
	//	*Column_Uint64
	//	*Column_Bytes
	//	*Column_Bool
	Value isColumn_Value `protobuf_oneof:"value"`
}

func (m *Column) Reset()                    { *m = Column{} }> {{{
func (m *Column) String() string            { return proto.CompactTextString(m) }
func (*Column) ProtoMessage()               {}
func (*Column) Descriptor() ([]byte, []int) { return fileDescriptor0, []int{2} }

type isColumn_Value interface {
	isColumn_Value()
}

type Column_String_ struct {
	String_ string `protobuf:"bytes,1,opt,name=string,oneof"`
}
type Column_Int32 struct {
	Int32 int32 `protobuf:"varint,2,opt,name=int32,oneof"`
}
type Column_Int64 struct {
	Int64 int64 `protobuf:"varint,3,opt,name=int64,oneof"`
}
type Column_Uint32 struct {
	Uint32 uint32 `protobuf:"varint,4,opt,name=uint32,oneof"`
}
type Column_Uint64 struct {
	Uint64 uint64 `protobuf:"varint,5,opt,name=uint64,oneof"`
}
type Column_Bytes struct {
	Bytes []byte `protobuf:"bytes,6,opt,name=bytes,proto3,oneof"`
}
type Column_Bool struct {
	Bool bool `protobuf:"varint,7,opt,name=bool,oneof"`
}

func (*Column_String_) isColumn_Value() {}
func (*Column_Int32) isColumn_Value()   {}
func (*Column_Int64) isColumn_Value()   {}
func (*Column_Uint32) isColumn_Value()  {}
func (*Column_Uint64) isColumn_Value()  {}
func (*Column_Bytes) isColumn_Value()   {}
func (*Column_Bool) isColumn_Value()    {}

func (m *Column) GetValue() isColumn_Value {
	if m != nil {
		return m.Value
	}
	return nil
}

func (m *Column) GetString_() string {
	if x, ok := m.GetValue().(*Column_String_); ok {
		return x.String_
	}
	return ""
}

func (m *Column) GetInt32() int32 {
	if x, ok := m.GetValue().(*Column_Int32); ok {
		return x.Int32
	}
	return 0
}

func (m *Column) GetInt64() int64 {
	if x, ok := m.GetValue().(*Column_Int64); ok {
		return x.Int64
	}
	return 0
}

func (m *Column) GetUint32() uint32 {
	if x, ok := m.GetValue().(*Column_Uint32); ok {
		return x.Uint32
	}
	return 0
}

func (m *Column) GetUint64() uint64 {
	if x, ok := m.GetValue().(*Column_Uint64); ok {
		return x.Uint64
	}
	return 0
}

func (m *Column) GetBytes() []byte {
	if x, ok := m.GetValue().(*Column_Bytes); ok {
		return x.Bytes
	}
	return nil
}

func (m *Column) GetBool() bool {
	if x, ok := m.GetValue().(*Column_Bool); ok {
		return x.Bool
	}
	return false
}

```


### Maps
Map的定义语法是
```protobuf
map<key_type, value_type> map_field = N;
```
其中，key_type可以是integral或者string类型（所以说，scalar类型中除了浮点类型和bytes类型的均可以）。
例子：
```protobuf
message Batch {
        bytes header = 1;
        repeated bytes payloads = 2;
        map<uint64, bytes> signatures = 3;
};
```
对应的编译后的go代码是
```go
type Batch struct {
	Header     []byte            `protobuf:"bytes,1,opt,name=header,proto3" json:"header,omitempty"`
	Payloads   [][]byte          `protobuf:"bytes,2,rep,name=payloads,proto3" json:"payloads,omitempty"`
	Signatures map[uint64][]byte `protobuf:"bytes,3,rep,name=signatures" json:"signatures,omitempty" protobuf_key:"varint,1,opt,name=key" protobuf_val:"bytes,2,opt,name=value,proto3"`
}

```
注意，其中，
- Map类型的成员变量不可以有`repeated`关键字，
- 如果maps的keys重复的话，则最后一个key才会被解析出来

### Packages
为了避免protocol message类型间名字重复带来的冲突，可以添加一个`package`关键字来避免
```protobuf
// 文件 core/chaincode/shim/chaincode.proto
package shim
```

### 定义Services
这个是用在RPC(Remote Procedure Call)远程进程调用系统中的，通过在.proto文件中定义RPC service接口，
protocol buffer编译器会生成service interface code和stubs。
比如说，我想要定义一个RPC service, 该service定义了methods
```protobuf
// 文件
syntax = "proto3";

package protos;

import "fabric.proto";
import "google/protobuf/empty.proto";

// Interface exported by the server.
service Openchain {

    // GetBlockchainInfo returns information about the blockchain ledger such as
    // height, current block hash, and previous block hash.
    rpc GetBlockchainInfo(google.protobuf.Empty) returns (BlockchainInfo) {}

    // GetBlockByNumber returns the data contained within a specific block in the
    // blockchain. The genesis block is block zero.
    rpc GetBlockByNumber(BlockNumber) returns (Block) {}

    // GetBlockCount returns the current number of blocks in the blockchain data
    // structure.
    rpc GetBlockCount(google.protobuf.Empty) returns (BlockCount) {}

    // GetPeers returns a list of all peer nodes currently connected to the target
    // peer.
    rpc GetPeers(google.protobuf.Empty) returns (PeersMessage) {}
}

// Specifies the block number to be returned from the blockchain.
message BlockNumber {

    uint64 number = 1;

}

// Specifies the current number of blocks in the blockchain.
message BlockCount {

    uint64 count = 1;

}
```

利用插件gRPC生成[api.pb.go](protos/api.pb.go),
service Openchain是对应接口类型的,会分别生成OpenchainClient和OpenChainServer两个接口类型的

首先，这个是客户端接口的定义及实现
```go

type OpenchainClient interface {
	// GetBlockchainInfo returns information about the blockchain ledger such as
	// height, current block hash, and previous block hash.
	GetBlockchainInfo(ctx context.Context, in *google_protobuf1.Empty, opts ...grpc.CallOption) (*BlockchainInfo, error)
	// GetBlockByNumber returns the data contained within a specific block in the
	// blockchain. The genesis block is block zero.
	GetBlockByNumber(ctx context.Context, in *BlockNumber, opts ...grpc.CallOption) (*Block, error)
	// GetBlockCount returns the current number of blocks in the blockchain data
	// structure.
	GetBlockCount(ctx context.Context, in *google_protobuf1.Empty, opts ...grpc.CallOption) (*BlockCount, error)
	// GetPeers returns a list of all peer nodes currently connected to the target
	// peer.
	GetPeers(ctx context.Context, in *google_protobuf1.Empty, opts ...grpc.CallOption) (*PeersMessage, error)
}


type openchainClient struct {
	cc *grpc.ClientConn
}

func NewOpenchainClient(cc *grpc.ClientConn) OpenchainClient {
	return &openchainClient{cc}
}

func (c *openchainClient) GetBlockchainInfo(ctx context.Context, in *google_protobuf1.Empty, opts ...grpc.CallOption) (*BlockchainInfo, error) {
	out := new(BlockchainInfo)
	err := grpc.Invoke(ctx, "/protos.Openchain/GetBlockchainInfo", in, out, c.cc, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *openchainClient) GetBlockByNumber(ctx context.Context, in *BlockNumber, opts ...grpc.CallOption) (*Block, error) {
	out := new(Block)
	err := grpc.Invoke(ctx, "/protos.Openchain/GetBlockByNumber", in, out, c.cc, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

//其余的方法的实现类似
```

当然😄，还有RPC的server端接口的定义及API的进一步包装，
可是，其中的GetBlockchainInfo等方法还是要我们手动实现的😭（毕竟是我们程序的逻辑，gRPC没有办法帮我们实现的）。
比如说，我实现了OpenchainServer的接口的话，则必须通过`RegisterOpenchainServer(s *grpc.Server, srv OpenchainServer)`
来把我的实现类型注册进去，这样它调用srv的方法的时候，就可以动态地调用我们实现的方法。

```go
// Server API for Openchain service

type OpenchainServer interface {
	// GetBlockchainInfo returns information about the blockchain ledger such as
	// height, current block hash, and previous block hash.
	GetBlockchainInfo(context.Context, *google_protobuf1.Empty) (*BlockchainInfo, error)
	// GetBlockByNumber returns the data contained within a specific block in the
	// blockchain. The genesis block is block zero.
	GetBlockByNumber(context.Context, *BlockNumber) (*Block, error)
	// GetBlockCount returns the current number of blocks in the blockchain data
	// structure.
	GetBlockCount(context.Context, *google_protobuf1.Empty) (*BlockCount, error)
	// GetPeers returns a list of all peer nodes currently connected to the target
	// peer.
	GetPeers(context.Context, *google_protobuf1.Empty) (*PeersMessage, error)
}

func RegisterOpenchainServer(s *grpc.Server, srv OpenchainServer) {
	s.RegisterService(&_Openchain_serviceDesc, srv)
}

func _Openchain_GetBlockchainInfo_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(google_protobuf1.Empty)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(OpenchainServer).GetBlockchainInfo(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/protos.Openchain/GetBlockchainInfo",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(OpenchainServer).GetBlockchainInfo(ctx, req.(*google_protobuf1.Empty))
	}
	return interceptor(ctx, in, info, handler)
}

//其余方法的包装API接口类似

```

### JSON Mapping
proto3还支持json编码，编码规则如下表所示(二者之间是安装类型对应的)

| proto3 类型 | JSON 对应的类型 | JSON 示例 | 注意 |
| ---         | ---    | ---| ---- |
| message     | object | {"fBar": v, "g": null, ...} | message类型会生成JSON对象，<br>message的成员变量的名字<br>会被映射成驼峰式的名字<br>（作为JSON对象的keys）|
| enum        | string | "FOO_BAR" | The name of the enum value as specified in proto is used |
| `map<K, V>` | object | {"k": v, ...} | 所有的keys都会被转换成字符串 |
| repeated V  | array  | `[v, ...]` | <b>null</b> is accecpted as the empty list `[]` |
| bool        | bool   | true, <br>false | |
| string      | string | "Hello World!"  | |
| bytes       | base64<br>string | "YWERSDFSDF+" | |
| int32,<br>fixed32,<br>uint32 | number | 1, -10, 0 | |
| int64,<br>fixed64,<br>uint64 | string | "1", "-10" | JSON value will be a decimal string.  Either numbers or strings are accepted |
| float,<br>double | number | 1.1, -10.0, 0, "NaN", "Infinity" | JSON value will be a number or one of the special string values "NaN". |
| Any         | object | {"@type": "url", "f": v, ...} | |
| Timestamp   | string | "1972-01-01T10:00:20.0212" | Uses RFC 3339, 输出Z-normalized, 小数位数一般是0，3，6或9位 |
| Duration    | string | "1.000340012s", "1s"       | RFC 3339, 当然也接受其他数目的位数 |
| Struct      | object | {...} | |
| Wrapper types | various types | 2, "2", "foo",<br> true, null, 0, ... | Wrappers use the same representation in JSON as the wrapped primitive type |
| FieldMask   | string | "f.fooBar,h" | See <b>fieldmask.proto</b> |
| ListValue   | array  | `[foo, bar, ...]` | |
| Value       | value  | | Any JSON value |
| NullValue   | null   | | JSON null |


### Options
主要有三种类型的options,
  1. file-level options: 
  ```protobuf
    option java_package = "com.exapmle.foo";
    option optimize_for = CODE_SIZE; 
  ```
  2. message-level options: 这些选项是写在message的定义里面的
  3. field-level options

### 编译生成特定语言的Classes

  protocol 编译器的语法简要如下：
  ```bash
  protoc --proto_path=IMPORT_PATH --cpp_out=DST_DIR --java_out=DST_DIR --python_out=DST_DIR --go_out=DST_DIR --ruby_out=DST_DIR --javanano_out=DST_DIR --objc_out=DST_DIR --csharp_out=DST_DIR path/to/file.proto
  ```
其中，
- **IMPORT_PATH** 是用来指定.proto文件中所import的其他.proto文件所在的目录。
`--proto_path=IMPORT-PATH`的同义简单版是`-I=IMPORT_PATH`

- 生成何种语言对应的classes定义：
  - `--cpp_out=DST_DIR`会生成C++代码在目录DST_DIR下的；
  - `--java_out=DST_DIR`会生成JAVA代码，放在目录DST_DIR里面；
  - `--go_out=DST_DIR`则会生成GO代码，放在目录DST_DIR里面；
  - 其它语言类似

[1]: https://developers.google.com/protocol-buffers/docs/gotutorial "protocol buffer GO 教程"
[2]: https://developers.google.com/protocol-buffers/docs/proto3 "protocol buffer version 3"

