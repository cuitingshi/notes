# Crypto 学习札记之 Operation Modes of Block Cipher
## 3. Block Mode 之 Cipher Feedback (CFB)
首先来看看 CFB 的定义, CFB 加密的数学定义如下：
$$ C_i = E_K(C_{i-1}) \oplus P_{i}, \ where\  C_0 = IV$$

CFB解密的数学定义如下：
$$ P_i = E_K(C_{i-1}) \oplus C_{i} \ where\  C_0 = IV$$

注意，上面的加密解密操作中异或的对象都是
<img src="http://chart.googleapis.com/chart?cht=tx&chl= E_K(C_{i-1}) " style="border:none;">
, 这样子的话，就赤裸裸地变成了[stream cipher](https://en.wikipedia.org/wiki/Stream_cipher), 有木有有木有😉

另外，CFB (还有 OFB 和 CTR，它们的共同点都是将一个block cipher 转换成了一个stream cipher) 相比于 CBC 模式，主要有两个优点：
1. the block cipher is only ever used in the encrypting direction,
2. the message does not need to be padded to a multiple of the cipher block size (though ciphertext stealing can also be used to make padding)


其中，CFB 模式中的加密操作的示意图如下：

![Cipher FeedBack (CFB) mode encryption](https://upload.wikimedia.org/wikipedia/commons/9/9d/CFB_encryption.svg)

而CBC模式中的解密操作的示意图如下：

![Cipher FeedBack (CFB) mode decryption](https://upload.wikimedia.org/wikipedia/commons/5/57/CFB_decryption.svg)


### 3.0 题外话 -- stream cipher
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

### 3.1 cipher包中对于CFB mode encryption 和 decryption 的实现
注意到之前的CFB的数学定义中的加密和解密操作中，
均是异或上前一个密文块经key加密后的块<img src="http://chart.googleapis.com/chart?cht=tx&chl= E_K(C_{i-1}) " style="border:none;">
,  因此，这个就可以当做一个stream cipher 了，
而其中的keystream 就是<img src="http://chart.googleapis.com/chart?cht=tx&chl= E_K(C_{i-1}) " style="border:none;">

golang的crypto/cipher包中的cfb.go已经实现了CFB模式，由于CFB模式属于stream cipher，加密和解密操作具有对称性，所以由变量decrypt 来
指定是加密还是解密操作，便可以了。另外，值得注意的是，
- 解密操作中由于需要用到前一块的密文，所以在对密文块i进行解密(对应 `xorBytes` 异或操作)前，
  需要先把该密文块i存到 `x.next` 中先
- 而对于加密操作，由于此次的密文i在下一块的加密中需要用到，所以需要在加密(对应 `xorBytes` 异或操作)之后，把密文块i存到`x.next`中，
  作为下一次加密操作的keystream <img src="http://chart.googleapis.com/chart?cht=tx&chl= E_K(C_{i-1})" style="border:none;"> 中
  的 <img src="http://chart.googleapis.com/chart?cht=tx&chl= C_{i-1}" style="border:none;">

具体的实现如下。：
```golang
type cfb struct {
	b       Block
	next    []byte
	out     []byte
	outUsed int

	decrypt bool
}

// 实现了StreamCipher接口中的 XORKeyStream 方法
func (x *cfb) XORKeyStream(dst, src []byte) {
	for len(src) > 0 {
		if x.outUsed == len(x.out) {
			x.b.Encrypt(x.out, x.next)
			x.outUsed = 0
		}

		if x.decrypt {
			// We can precompute a larger segment of the
			// keystream on decryption. This will allow
			// larger batches for xor, and we should be
			// able to match CTR/OFB performance.
			copy(x.next[x.outUsed:], src)
		}
		n := xorBytes(dst, src, x.out[x.outUsed:])
		if !x.decrypt {
			copy(x.next[x.outUsed:], dst)
		}
		dst = dst[n:]
		src = src[n:]
		x.outUsed += n
	}
}
```

### 3.2 CFB模式的使用
前面已经说明了CFB模式会使得block cipher 变成一个 stream cipher，
注意下面如何使用CFB进行加密和解密操作,

1. 先使用下面的方法生成一个 stream cipher 接口 -- Stream
    - 对于要使用CFB加密的话，需要调用函数 `NewCFBEncrypter(block Block, iv []byte) Stream` 来生成一个用于加密的 stream cipher -- CFBEncrypter;
    - 对于解密的话，需要调用函数 `NewCFBDecrypter(block Block, iv []byte) Stream` 来生成一个用于解密的 stream cipher -- CFBDecrypter;
2. 然后调用 cfb 对于 Stream 接口的 `XORKeyStream` 方法，进行相应的加密或者解密操作（其实都是异或上 keystream ~\(≧▽≦)/~啦啦啦）

```golang

// NewCFBEncrypter returns a Stream which encrypts with cipher feedback mode,
// using the given Block. The iv must be the same length as the Block's block
// size.
func NewCFBEncrypter(block Block, iv []byte) Stream {
	return newCFB(block, iv, false)
}

// NewCFBDecrypter returns a Stream which decrypts with cipher feedback mode,
// using the given Block. The iv must be the same length as the Block's block
// size.
func NewCFBDecrypter(block Block, iv []byte) Stream {
	return newCFB(block, iv, true)
}

func newCFB(block Block, iv []byte, decrypt bool) Stream {
	blockSize := block.BlockSize()
	if len(iv) != blockSize {
		// stack trace will indicate whether it was de or encryption
		panic("cipher.newCFB: IV length must equal block size")
	}
	x := &cfb{
		b:       block,
		out:     make([]byte, blockSize),
		next:    make([]byte, blockSize),
		outUsed: blockSize,
		decrypt: decrypt,
	}
	copy(x.next, iv)

	return x
}
```

