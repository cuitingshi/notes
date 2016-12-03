## 2. Block Mode 之 CBC 
首先来看看 CBC 的定义, CBC加密的数学定义如下：

<img src="http://chart.googleapis.com/chart?cht=tx&chl= C_i = E_K(P_i \oplus C_{i-1}) \\ C_0 = IV." style="border:none;">

CBC解密的数学定义如下：

<img src="http://chart.googleapis.com/chart?cht=tx&chl= P_i = D_K(C_i) \oplus C_{i-1} \\ C_0 = IV." style="border:none;">

其中，CBC模式中的加密操作的示意图如下：

![Cipher Block Chaining (CBC) mode encryption](https://upload.wikimedia.org/wikipedia/commons/8/80/CBC_encryption.svg)

而CBC模式中的解密操作的示意图如下：

![Cipher Block Chaining (CBC) mode decryption](https://upload.wikimedia.org/wikipedia/commons/2/2a/CBC_decryption.svg)


### 2.1. cipher包中对于CBC mode encryption 和 decryption 的实现
golang的crypto/cipher包中已经实现了CBC模式，其中，
- 对于CBC模式中的加密操作，`cbcEncrypter`(即cbc)实现了前面定义的`BlockMode`接口中的`CryptBlock(dst, src []byte)`，
- 对于CBC模式中的解密操作，`cbcDecrypter`(即cbc)实现了前面定义的`BlockMode`接口中的`CryptBlock(dst, src []byte)`

首先来看看CBC mode encryption的实现:

#### 2.1.1. CBC mode encryption
CBC模式中的加密操作的示意图如下：

![Cipher Block Chaining (CBC) mode encryption](https://upload.wikimedia.org/wikipedia/commons/8/80/CBC_encryption.svg)

CBC加密的数学定义如下：

<img src="http://chart.googleapis.com/chart?cht=tx&chl= C_i = E_K(P_i \oplus C_{i-1}) \\ C_0 = IV." style="border:none;">

注意下面的`CryptBlocks`方法的实现中的`for`循环里面的`xorBytes`操作、加密操作`x.b.Encrypt`分别对应上面的数学定义中的异或和加密操作。

```golang
type cbc struct {
	b         Block
	blockSize int
	iv        []byte
	tmp       []byte
}
type cbcEncrypter cbc

// 实现了BlockMode接口中的BlockSize()方法
func (x *cbcEncrypter) BlockSize() int { return x.blockSize }

// 实现了BlockMode接口中的CryptBlocks()方法
func (x *cbcEncrypter) CryptBlocks(dst, src []byte) {
	if len(src)%x.blockSize != 0 {
		panic("crypto/cipher: input not full blocks")
	}
	if len(dst) < len(src) {
		panic("crypto/cipher: output smaller than input")
	}

	iv := x.iv

	for len(src) > 0 {
		// Write the xor to dst, then encrypt in place.
		xorBytes(dst[:x.blockSize], src[:x.blockSize], iv)
		x.b.Encrypt(dst[:x.blockSize], dst[:x.blockSize])

		// Move to the next block with this block as the next iv.
		iv = dst[:x.blockSize]
		src = src[x.blockSize:]
		dst = dst[x.blockSize:]
	}

	// Save the iv for the next CryptBlocks call.
	copy(x.iv, iv)
}

func (x *cbcEncrypter) SetIV(iv []byte) {
	if len(iv) != len(x.iv) {
		panic("cipher: incorrect length IV")
	}
	copy(x.iv, iv)
}

// 如果某个block cipher 实现了cbcEncAble接口的话, 则会使用它自己实现的CBC 加密操作，
// 否则使用cbcEncrypter实现的CBC加密操作。
// NewCBCEncrypter returns a BlockMode which encrypts in cipher block chaining
// mode, using the given Block. The length of iv must be the same as the
// Block's block size.
func NewCBCEncrypter(b Block, iv []byte) BlockMode {
	if len(iv) != b.BlockSize() {
		panic("cipher.NewCBCEncrypter: IV length must equal block size")
	}
	if cbc, ok := b.(cbcEncAble); ok {
		return cbc.NewCBCEncrypter(iv)
	}
	return (*cbcEncrypter)(newCBC(b, iv))
}

func newCBC(b Block, iv []byte) *cbc {
	return &cbc{
		b:         b,
		blockSize: b.BlockSize(),
		iv:        dup(iv),
		tmp:       make([]byte, b.BlockSize()),
	}
}


```

#### 2.1.2. CBC mode decryption
CBC模式中的解密操作的示意图如下：

![Cipher Block Chaining (CBC) mode decryption](https://upload.wikimedia.org/wikipedia/commons/2/2a/CBC_decryption.svg)

CBC解密的数学定义如下：

<img src="http://chart.googleapis.com/chart?cht=tx&chl= P_i = D_K(C_i) \oplus C_{i-1} \\ C_0 = IV." style="border:none;">

同样, `cbcDecrypter`实现了`BlockMode`接口中定义的两个方法, 所以cbcDecrypter也属于BlockMode。
```golang
// A BlockMode represents a block cipher running in a block-based mode (CBC,
// ECB etc).
type BlockMode interface {
	// BlockSize returns the mode's block size.
	BlockSize() int

	// CryptBlocks encrypts or decrypts a number of blocks. The length of
	// src must be a multiple of the block size. Dst and src may point to
	// the same memory.
	CryptBlocks(dst, src []byte)
}

```

注意，由于CBC的解密操作需要用到前一个密文块，所以为了避免多余的复制，需要从最后一块开始解密（上图需要从右至左看😁）。
此外，与加密过程反向的是，先对块进行解密，得到（plaintext xor prev_ciphertext）， 然后再进行异或操作-- （plaintext xor prev_ciphertext) xor prev_ciphertext
，便可以得到plaintext，有木有觉得异或操作很🐂吖😄
```golang
type cbc struct {
	b         Block
	blockSize int
	iv        []byte
	tmp       []byte
}
type cbcDecrypter cbc

// 实现了BlockMode接口中的BlockSize()方法
func (x *cbcDecrypter) BlockSize() int { return x.blockSize }

// 实现了BlockMode 接口中的CryptBlocks()方法
func (x *cbcDecrypter) CryptBlocks(dst, src []byte) {
	if len(src)%x.blockSize != 0 {
		panic("crypto/cipher: input not full blocks")
	}
	if len(dst) < len(src) {
		panic("crypto/cipher: output smaller than input")
	}
	if len(src) == 0 {
		return
	}

	// For each block, we need to xor the decrypted data with the previous block's ciphertext (the iv).
	// To avoid making a copy each time, we loop over the blocks BACKWARDS.
	end := len(src)
	start := end - x.blockSize
	prev := start - x.blockSize

	// Copy the last block of ciphertext in preparation as the new iv.
	copy(x.tmp, src[start:end])

	// Loop over all but the first block.
	for start > 0 {
		x.b.Decrypt(dst[start:end], src[start:end])
		xorBytes(dst[start:end], dst[start:end], src[prev:start])

		end = start
		start = prev
		prev -= x.blockSize
	}

	// The first block is special because it uses the saved iv.
	x.b.Decrypt(dst[start:end], src[start:end])
	xorBytes(dst[start:end], dst[start:end], x.iv)

	// Set the new iv to the first block we copied earlier.
	x.iv, x.tmp = x.tmp, x.iv
}

func (x *cbcDecrypter) SetIV(iv []byte) {
	if len(iv) != len(x.iv) {
		panic("cipher: incorrect length IV")
	}
	copy(x.iv, iv)
}

// NewCBCDecrypter returns a BlockMode which decrypts in cipher block chaining
// mode, using the given Block. The length of iv must be the same as the
// Block's block size and must match the iv used to encrypt the data.
func NewCBCDecrypter(b Block, iv []byte) BlockMode {
	if len(iv) != b.BlockSize() {
		panic("cipher.NewCBCDecrypter: IV length must equal block size")
	}
	if cbc, ok := b.(cbcDecAble); ok { //如果block cipher 实现了cbcDecAble接口，则使用其自定义的cbcCBC mode decryption操作的实现
		return cbc.NewCBCDecrypter(iv) 
	}
	return (*cbcDecrypter)(newCBC(b, iv)) //否则使用默认的实现，cbcDecrypter
}

func newCBC(b Block, iv []byte) *cbc {
	return &cbc{
		b:         b,
		blockSize: b.BlockSize(),
		iv:        dup(iv),
		tmp:       make([]byte, b.BlockSize()),
	}
}

```

### 2.2 自定义的CBC连接模式的实现
当然，也可以不使用cipher包中对于CBC模式的实现，如果block cipher想要使用自己实现的CBC连接模式的话，
对于CBC加密操作，需要实现两个接口：
1. BlockMode

首先需要实现接口`BlockMode`中定义的两个方法，完成自定义的连接模式的加密操作
```golang
// A BlockMode represents a block cipher running in a block-based mode (CBC,
// ECB etc).
type BlockMode interface {
	// BlockSize returns the mode's block size.
	BlockSize() int

	// CryptBlocks encrypts or decrypts a number of blocks. The length of
	// src must be a multiple of the block size. Dst and src may point to
	// the same memory.
	CryptBlocks(dst, src []byte)
}
```

2. cbcEncAble

然后，需要实现cbcEncAble接口
```golang
type cbcEncrypter cbc

// block cipher 需要实现该加密接口
// cbcEncAble is an interface implemented by ciphers that have a specific
// optimized implementation of CBC encryption, like crypto/aes.
// NewCBCEncrypter will check for this interface and return the specific
// BlockMode if found.
type cbcEncAble interface {
	NewCBCEncrypter(iv []byte) BlockMode
}
```

同样，对于CBC解密操作，同样需要实现两个接口：
1. BlockMode
  这里的`BlockMode中的CrypBlocks(dst, src []byte)`需要实现CBC的解密操作。
2. cbcDecAble

```golang
// block cipher 需要实现该解密接口
// cbcDecAble is an interface implemented by ciphers that have a specific
// optimized implementation of CBC decryption, like crypto/aes.
// NewCBCDecrypter will check for this interface and return the specific
// BlockMode if found.
type cbcDecAble interface {
	NewCBCDecrypter(iv []byte) BlockMode
}
```

这样子的话，block cipher 就可以在兼容现有的cipher包实现的CBC模式的情况下，
- 对于加密，直接使用cipher包中统一的接口`NewCBCEncrypter(b Block, iv []byte) BlockMode`来使用CBC模式了，
  只不过在加密的时候调用的BlockMode是block cipher自己实现的`CryptBlocks(dst, src []byte)`方法；
- 对于解密，也是可以使用cipher包中统一的接口`NewCBCDecrypter(b Block, iv []byte) BlockMode`，
  然后解密的时候调用的是自己实现的BlockMode接口中的`CryptBlocks(dst, src []byte)`方法

```golang
// 生成负责加密的
// NewCBCEncrypter returns a BlockMode which encrypts in cipher block chaining
// mode, using the given Block. The length of iv must be the same as the
// Block's block size.
func NewCBCEncrypter(b Block, iv []byte) BlockMode {
	if len(iv) != b.BlockSize() {
		panic("cipher.NewCBCEncrypter: IV length must equal block size")
	}
	if cbc, ok := b.(cbcEncAble); ok { //如果block cipher 实现了cbcEncAble接口，则使用其自定义的cbc mode encryption操作
		return cbc.NewCBCEncrypter(iv)
	}
	return (*cbcEncrypter)(newCBC(b, iv)) // 否则的话，就使用cipher包中已经实现的cbc mode encryption操作
}


// 生成负责解密的
// NewCBCDecrypter returns a BlockMode which decrypts in cipher block chaining
// mode, using the given Block. The length of iv must be the same as the
// Block's block size and must match the iv used to encrypt the data.
func NewCBCDecrypter(b Block, iv []byte) BlockMode {
	if len(iv) != b.BlockSize() {
		panic("cipher.NewCBCDecrypter: IV length must equal block size")
	}
	if cbc, ok := b.(cbcDecAble); ok {
		return cbc.NewCBCDecrypter(iv)
	}
	return (*cbcDecrypter)(newCBC(b, iv))
}

```

