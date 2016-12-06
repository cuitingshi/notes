# Crypto 学习札记之 Operation Modes of Block Cipher
## 5. Block Mode 之 Counter Mode (CTR)
CTR mode (CM) 有两种模式：

1. interger counter mode (ICM);
2. segmented integer counter (SIC) mode

Like OFB,  <font color="red">*Counter mode*</font> (CTR mode) makes a block cipher into a syncrhonous stream cipher. 
It generates the next [key stream](https://en.wikipedia.org/wiki/Keystream) block by encrypting successive values of a 
"counter". The counter can be any function which produces a sequence which is guaranteed not to repeat for a long time, 
  although an actual increment-by-one counter is the simplest and most popular. 

CTR mode 跟 OFB 虽然性质上类型，但是CTR mode 还允许 a random access property during decryption. 这样，
对于可以并行加密blocks的多处理器的机器，CTR mode 是非常不错的。另外，
- 对于 random nonce, 即 <font color="purple"><b>IV/nonce</b></font> 是随机的，那么他们可以结合使用(concatenation, addition, or XOR) 操作的counter 
来生成用于加密的actual unique counter block. 
- 对于non-random nonce (比如 a packet counter), nonce 和 counter 应该连接起来。
  比如说，如果counter block 是128位的话，可以将nonce 存储在高64位，counter 存在64位。


首先来看看 Counter mode 中的加密操作，示意图如下：

![Counter (CTR) mode encryption](https://upload.wikimedia.org/wikipedia/commons/4/4d/CTR_encryption_2.svg)

而 Counter mode 中的解密操作如下图所示：

![Counter (CTR) mode decryption](https://upload.wikimedia.org/wikipedia/commons/3/3c/CTR_decryption_2.svg) 

上边的Nonce 其实相当于其他模式中的initialization vector (IV), 此外值得注意的是,
CTR mode 中的加密和解密操作都是并行的，这点是非常不同于前面所说的 CBC, CFB, OFB 等模式的。

### 5.0 题外话 -- stream cipher
A stream cipher is a symmetric key cipher where plaintext digits are combined with a pseudorandom cipher digit stream (keystream).
其中的combining 操作通常是采用异或运算。

此外，其中的[keystream](https://en.wikipedia.org/wiki/Keystream)指的是a stream of random or pseudorandom characters that are combined
with a plaintext message to produce an encrypted message (the ciphertext)。值得注意的是，keystream 中的 characters 可以是bits, bytes, numbers,
也可以是实际的字符（比如A-Z），keystream 是依使用情况而定的。

golang的cipher包中将stream cipher定义成一个接口，注意只有一个方法哦，想想异或操作的特性，所以加密和解密均是异或上keystream就可以了😄，
又一次对于异或操作表示佩服↖(^ω^)↗.注意，keystream 是存储在cipher中的，接口的定义如下：
```golang
// A Stream represents a stream cipher.
type Stream interface {
	// XORKeyStream XORs each byte in the given slice with a byte from the
	// cipher's key stream. Dst and src may point to the same memory.
	// If len(dst) < len(src), XORKeyStream should panic. It is acceptable
	// to pass a dst bigger than src, and in that case, XORKeyStream will
	// only update dst[:len(src)] and will not touch the rest of dst.
	XORKeyStream(dst, src []byte)
}

```

### 5.1 cipher包中对于CTR  mode encryption 和 decryption 的实现
golang的crypto/cipher包中的ctr.go已经实现了 CTR mode，由于CTR mode 属于stream cipher，加密和解密操作中异或的对象都相同，所以可以实现如下：

```golang
type ctr struct {
	b       Block
	ctr     []byte
	out     []byte
	outUsed int
}

const streamBufferSize = 512

// ctrAble is an interface implemented by ciphers that have a specific optimized
// implementation of CTR, like crypto/aes. NewCTR will check for this interface
// and return the specific Stream if found.
type ctrAble interface {
	NewCTR(iv []byte) Stream
}

// 如果block cipher 自己实现了CTR mode（需实现Stream 接口中的方法进行加密解密操作，还需得实现 ctrAble 接口）
// 这样便可以使用block cipher 自己关于CTR mode 的实现
// 否则，默认使用cipher 包中ctr 所实现的方法。
// NewCTR returns a Stream which encrypts/decrypts using the given Block in
// counter mode. The length of iv must be the same as the Block's block size.
func NewCTR(block Block, iv []byte) Stream {
	if ctr, ok := block.(ctrAble); ok { 
		return ctr.NewCTR(iv)
	}
	if len(iv) != block.BlockSize() {
		panic("cipher.NewCTR: IV length must equal block size")
	}
	bufSize := streamBufferSize
	if bufSize < block.BlockSize() {
		bufSize = block.BlockSize()
	}
	return &ctr{
		b:       block,
		ctr:     dup(iv),
		out:     make([]byte, 0, bufSize),
		outUsed: 0,
	}
}

// 注意到，如果使用的streamBufferSize 大于每次处理的block的大小的话，
// 那么会提前计算好每次操作中的keystream，暂存在x.out中，还是觉得很妙😄
// 不同于其他mode, 此处需要每次都改变counter ctr, 注意counter的改变有点随机哟😄
func (x *ctr) refill() {
	remain := len(x.out) - x.outUsed
	copy(x.out, x.out[x.outUsed:])
	x.out = x.out[:cap(x.out)]
	bs := x.b.BlockSize()
	for remain <= len(x.out)-bs {
		x.b.Encrypt(x.out[remain:], x.ctr)
		remain += bs

		// Increment counter
		for i := len(x.ctr) - 1; i >= 0; i-- {
			x.ctr[i]++
			if x.ctr[i] != 0 {
				break
			}
		}
	}
	x.out = x.out[:remain]
	x.outUsed = 0
}

func (x *ctr) XORKeyStream(dst, src []byte) {
	for len(src) > 0 {
		if x.outUsed >= len(x.out)-x.b.BlockSize() {
			x.refill()
		}
		n := xorBytes(dst, src, x.out[x.outUsed:])
		dst = dst[n:]
		src = src[n:]
		x.outUsed += n
	}
}
```

### 5.2 CTR mode 的使用
前面已经说明了 CTR 模式会使得block cipher 变成一个 stream cipher，
注意下面如何使用CTR mode 进行加密和解密操作, 区别只在于输入的数据是明文数据还是密文数据, 
不论block cipher 实现CTR mode 与否，均首先需要统一调用`NewCTR(b Block, iv []byte) Stream`来生成Strem
接口，然后再调用 ctr 对于 Stream 接口的实现中的 `XORKeyStream` 方法，进行相应的加密或者解密操作.
其实都是异或上 keystream (这里对应 `counter`)~\(≧▽≦)/~啦啦啦. 

当然，block cipher 可以自己实现CTR mode，不过得实现两个接口:
1. Stream
  需实现该接口中的`XORKeyStream`来实现CTR mode 中的加密解密操作
2. ctrAble
  这样用户在`NewCTR(block Block, iv []byte) Stream`的时候，便可以使用block cipher <b>Block</b>中的实现的`Stream`接口中的方法.


```golang
type ctr struct {
	b       Block
	ctr     []byte
	out     []byte
	outUsed int
}

const streamBufferSize = 512

// ctrAble is an interface implemented by ciphers that have a specific optimized
// implementation of CTR, like crypto/aes. NewCTR will check for this interface
// and return the specific Stream if found.
type ctrAble interface {
	NewCTR(iv []byte) Stream
}

// 如果block cipher 自己实现了CTR mode（需实现Stream 接口中的方法进行加密解密操作，还需得实现 ctrAble 接口）
// 这样便可以使用block cipher 自己关于CTR mode 的实现
// 否则，默认使用cipher 包中ctr 所实现的方法。
// NewCTR returns a Stream which encrypts/decrypts using the given Block in
// counter mode. The length of iv must be the same as the Block's block size.
func NewCTR(block Block, iv []byte) Stream {
	if ctr, ok := block.(ctrAble); ok { 
		return ctr.NewCTR(iv)
	}
	if len(iv) != block.BlockSize() {
		panic("cipher.NewCTR: IV length must equal block size")
	}
	bufSize := streamBufferSize
	if bufSize < block.BlockSize() {
		bufSize = block.BlockSize()
	}
	return &ctr{
		b:       block,
		ctr:     dup(iv),
		out:     make([]byte, 0, bufSize),
		outUsed: 0,
	}
}

```

