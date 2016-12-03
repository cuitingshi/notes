## 4. Block Mode 之 Output Feedback
The <font color="red">*Output Feedback*</font> (OFB) mode makes a block cipher into a syncrhonous stream cipher.
OFB 首先生成keystream blocks, 然后再跟plaintext blocks 做异或操作生成密文。
由于异或操作的对称性，加密操作和解密操作实际上是一样的。

首先来看看 OFB 的定义, OFB 加密的数学定义如下：

<img src="http://chart.googleapis.com/chart?cht=tx&chl= C_j = P_j \oplus E_K( I_{j-1} ) " style="border:none;">

OFB解密的数学定义如下：

<img src="http://chart.googleapis.com/chart?cht=tx&chl= P_j = C_j \oplus E_K( I_{j-1} ) " style="border:none;">

其中的输出反馈是

<img src="http://chart.googleapis.com/chart?cht=tx&chl= I_j = E_K(I_{j-1}) \\ I_0 = IV" style="border:none;">


值得注意的是，上面的加密解密操作中异或的对象都是
<img src="http://chart.googleapis.com/chart?cht=tx&chl= E_K(I_{j-1}) " style="border:none;">
, 这样子的话，就赤裸裸地变成了[stream cipher](https://en.wikipedia.org/wiki/Stream_cipher), 有木有有木有😉



对于输出反馈模式 OFB mode 中的加密操作，示意图如下：

![Output FeedBack (OFB) mode encryption](https://upload.wikimedia.org/wikipedia/commons/b/b0/OFB_encryption.svg)

而 OFB 模式中的解密操作的示意图如下：

![Output FeedBack (OFB) mode decryption](https://upload.wikimedia.org/wikipedia/commons/f/f5/OFB_decryption.svg)


### 4.0 题外话 -- stream cipher
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

### 4.1 cipher包中对于OFB  mode encryption 和 decryption 的实现
注意到之前的CFB的数学定义中的加密和解密操作中，
异或的对象均是经过最初的 `IV` 经过加密逐步演进而来的, 对于明文<img src="http://chart.googleapis.com/chart?cht=tx&chl= P_j" style="border:none;">
 或者密文<img src="http://chart.googleapis.com/chart?cht=tx&chl= C_j" style="border:none;">
, 每次异或的对象均是 <img src="http://chart.googleapis.com/chart?cht=tx&chl= E_K(I_{j-1}) " style="border:none;">
,  因此，这个就可以当做一个stream cipher 了，每次的keystream 就是<img src="http://chart.googleapis.com/chart?cht=tx&chl= E_K(I_{j-1}) " style="border:none;">

golang的crypto/cipher包中的cfb.go已经实现了OFB模式，由于OFB模式属于stream cipher，加密和解密操作中异或的对象都相同，所以可以实现如下：

```golang
type ofb struct {
	b       Block
	cipher  []byte
	out     []byte
	outUsed int
}

const streamBufferSize = 512

// NewOFB returns a Stream that encrypts or decrypts using the block cipher b
// in output feedback mode. The initialization vector iv's length must be equal
// to b's block size.
func NewOFB(b Block, iv []byte) Stream {
	blockSize := b.BlockSize()
	if len(iv) != blockSize {
		return nil
	}
	bufSize := streamBufferSize
	if bufSize < blockSize {
		bufSize = blockSize
	}
	x := &ofb{
		b:       b,
		cipher:  make([]byte, blockSize),
		out:     make([]byte, 0, bufSize),
		outUsed: 0,
	}

	copy(x.cipher, iv)
	return x
}

// 注意到，如果使用的streamBufferSize 大于每次处理的block的大小的话，
// 那么会提前计算好每次操作中的keystream，暂存在x.out中，有木有很妙啊😄
func (x *ofb) refill() {
	bs := x.b.BlockSize()
	remain := len(x.out) - x.outUsed
	if remain > x.outUsed {
		return
	}
	copy(x.out, x.out[x.outUsed:])
	x.out = x.out[:cap(x.out)]
	for remain < len(x.out)-bs {
		x.b.Encrypt(x.cipher, x.cipher)
		copy(x.out[remain:], x.cipher)
		remain += bs
	}
	x.out = x.out[:remain]
	x.outUsed = 0
}

func (x *ofb) XORKeyStream(dst, src []byte) {
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

### 4.2 OFB模式的使用
前面已经说明了OFB模式会使得block cipher 变成一个 stream cipher，
注意下面如何使用OFB进行加密和解密操作, 区别只在于输入的数据是明文数据还是密文数据, 统一的都是调用`NewOFB(b Block, iv []byte)`来生成Strem
接口，然后再调用 ofb 对于 Stream 接口的实现中的 `XORKeyStream` 方法，进行相应的加密或者解密操作
（其实都是异或上 keystream <img src="http://chart.googleapis.com/chart?cht=tx&chl= E_K(I_{j-1}) " style="border:none;">
~\(≧▽≦)/~啦啦啦）

```golang
type ofb struct {
	b       Block
	cipher  []byte
	out     []byte
	outUsed int
}

// NewOFB returns a Stream that encrypts or decrypts using the block cipher b
// in output feedback mode. The initialization vector iv's length must be equal
// to b's block size.
func NewOFB(b Block, iv []byte) Stream {
	blockSize := b.BlockSize()
	if len(iv) != blockSize {
		return nil
	}
	bufSize := streamBufferSize
	if bufSize < blockSize {
		bufSize = blockSize
	}
	x := &ofb{
		b:       b,
		cipher:  make([]byte, blockSize),
		out:     make([]byte, 0, bufSize),
		outUsed: 0,
	}

	copy(x.cipher, iv)
	return x
}

```

