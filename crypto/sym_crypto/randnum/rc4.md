> 2016年12月 6日 星期二 11时58分53秒 CST

# RC4 算法
RC4 是一种秘钥长度可变、面向字节操作的流密码。SSL/TLS协议、WEP、WPA中均有所应用

## RC4 Cipher
RC4 通过生成伪随机位流作为keystream, 
- 加密：该 keystream 与明文 plaintext 做异或操作从而得到密文 ciphertext;
- 解密：该 keystream 与密文 ciphertext 做异或操作从而得到明文 plaintext;

所以，RC4 的重点在于如何生成 keystream 呢？🤔

其实，to generate the keystream, the cipher makes use of a secret internal state which consists of two parts:
1. A permutation of all 256 possible bytes (对应下面的 S)
2. Two 8-bit index-pointers (对应下面的 i 和 j)

Anyway, 生成 keystream 只要有两部分：
1. Key Scheduling Algorithm (KSA): The permuation S 一开始会由一个长度可变的秘钥 key 进行初始化（key 的长度一般为40到2048 bits），
然后使用 key-scheduling algorithm (KSA) 对 S 做转换，
2. Pseudo-Random Generation Algorithm (PRGA): 最后在使用 伪随机数生成算法 (PRGA) 来生成 keystream.


### Key-Scheduling Algorithm (KSA)
- S: The key-scheduling algorithm is used initialize the permutation in the array S. 
- len(key): the number of bytes in the key, 长度范围可以为 [1, 256]，不过一般是 [5, 256].

算法可以表示如下：
```golang
var S [256]uint32

for i := 0; i < 256; i++ {
  S[i] = uint32(i)
}

var j uint8 = 0
for i := 0; i < 256; i++{
  j += S[i] + key[i%len(key)]
  S[i], S[j] = S[j], S[i]
}
```

### Pseudo-Random Generation Algorithm (PRGA)
- src: the plaintext or the ciphertext
- keystream: the keystream

算法可以表示如下：
```golang
var i uint8 = 0
var j uint8 = 0
var keystream []byte
for k, v := range src {
  i += 1
  j += uint8(S[i])
  S[i], S[j] = S[j], S[i]
  keysream[k] = S[ uint8(S[i] + S[j]) ]
}
```
😁，有没有发现，其实上面的keystream可以作为随机数，因此也可以把 基于 RC4 来实现 PRNG

## RC4 cipher 的实现
go 语言中的 crypto/rc4 实现了rc4 cipher，代码如下：

```golang
import "strconv"

// A Cipher is an instance of RC4 using a particular key.
type Cipher struct {
  s [256]uint32
  i, j uint8
}

type KeySizeError int

func (k KeySizeError) Error() string {
  return "crypto/rc4: invalid key" + strconv.Itoa(int(k))
}

// NewCipher creates and returns a new Cipher. The argument should be the RC4 key,
// at least 1 byte and at most 256 bytes.
func NewCipher(key []byte) (*Cipher, error){
  k := len(key)
  if k<1 || k>256 {
    return nil, KeySizeError(k)
  }
  
  // Key-scheduling algorithm (KSA)
  // 1. initialize s as identity permutation
  var c Cipher
  for i:=0; i<256; i++ {
    c.s[i] = uint32(i)
  }
  // 2. mixes s with the bytes of the key
  var j uint8 = 0
  for i:=0; i<256; i++ {
    j += uint8(c.s[i]) + key[i%k]
    c.s[i], c.s[j] = c.s[j], c.s[i]
  }
  return &c, nil
}

// Reset zeros the key data so that it will no longer appear in the process's memory.
func (c *Cipher) Reset() {
  for i := range c.s {
    c.s[i] = 0
  }
  c.i, c.j = 0, 0
}

//xorKeyStreamGeneric set dst to the result of XORing src with the key stream.
// Dst and src may be the same slice but otherwise should not overlap
//
// This is the pure Go version. rc4_{amd64, 386, arm}* contain assembly implementations.
// This is here for tests and to prevent bitrot.
func (c *Cipher) xorKeyStreamGeneric(dst, src []byte) {
  i, j := c.i, c.j
  for k, v := range src {
    i += 1
    j += uint8(c.s[i])
    c.s[i], c.s[j] = c.s[j], c.s[i]
    dst[k] = v ^ uint8(c.s[uint8(c.s[i]+c.s[j])])
  }
  c.i, c.j = i, j
}
```

与汇编语言的接口如下：
```golang
// +build amd64 amd64p32 arm,!nacl 386

func xorKeyStream(dst, src *byte, n int, state *[256]uint32, i, j *uint8)

// XORKeyStream sets dst to the result of XORing src with the key stream.
// Dst and src may be the same slice but otherwise should not overlap.
func (c *Cipher) XORKeyStream(dst, src []byte) {
  if len(src) == 0 {
    return 
  }
  xorKeySteream(&dst[0], &src[0], len(src), &c.s, &c.i, &c.j)
}
```

对应 [AMD64 处理器上的汇编语言的优化版](http://www.zorinaq.com/papers/rc4-amd64.html)实现如下：
```arm
// RC4 implementation optimized for AMD64 processors.
TEXT .xorKeyStream(SB),NOSPLIT, $0
  MOVQ n+16(FP), BX   // rbx = ARG(len)
  MOVQ src+8(FP), SI  // in = ARG(in)
  MOVQ dst+0(FP), DI  // out = ARG(out)
  MOVQ state+24(FP), BP
  MOVQ i+32(FP), AX
  MOVBQZX 0(AX), CX   // x = *xp
  MOVQ j+40(FP), AX
  MOVBQZX 0(AX), DX   // y = *yp

  LEAQ (SI)(BX*1), R9 //limit = in + len

l1:	CMPQ	SI,		R9		// cmp in with in+len
	JGE	finished			  // jump if (in >= in+len)

	INCB	CX
	EXTEND(CX)
	TESTL	$15,		CX
	JZ	wordloop

	MOVBLZX	(BP)(CX*4),	AX

	ADDB	AX,		DX		  // y += tx
	EXTEND(DX)
	MOVBLZX	(BP)(DX*4),	BX		// ty = d[y]
	MOVB	BX,		(BP)(CX*4)	  // d[x] = ty
	ADDB	AX,		BX	        	// val = ty+tx
	EXTEND(BX)
	MOVB	AX,		(BP)(DX*4)	  // d[y] = tx
	MOVBLZX	(BP)(BX*4),	R8		// val = d[val]
	XORB	(SI),		R8		      // xor 1 byte
	MOVB	R8,		(DI)
	INCQ	SI				      // in++
	INCQ	DI				      // out++
	JMP l1

wordloop:
	SUBQ	$16,		R9
	CMPQ	SI,		R9
	JGT	end

start:
	ADDQ	$16,		SI		// increment in
	ADDQ	$16,		DI		// increment out


	// Each KEYROUND generates one byte of key and
	// inserts it into an XMM register at the given 16-bit index.
	// The key state array is uint32 words only using the bottom
	// byte of each word, so the 16-bit OR only copies 8 useful bits.
	// We accumulate alternating bytes into X0 and X1, and then at
	// the end we OR X1<<8 into X0 to produce the actual key.
	//
	// At the beginning of the loop, CX%16 == 0, so the 16 loads
	// at state[CX], state[CX+1], ..., state[CX+15] can precompute
	// (state+CX) as R12 and then become R12[0], R12[1], ... R12[15],
	// without fear of the byte computation CX+15 wrapping around.
	//
	// The first round needs R12[0], the second needs R12[1], and so on.
	// We can avoid memory stalls by starting the load for round n+1
	// before the end of round n, using the LOAD macro.
	LEAQ	(BP)(CX*4),	R12

#define KEYROUND(xmm, load, off, r1, r2, index) \
	MOVBLZX	(BP)(DX*4),	R8; \
	MOVB	r1,		(BP)(DX*4); \
	load((off+1), r2); \
	MOVB	R8,		(off*4)(R12); \
	ADDB	r1,		R8; \
	EXTEND(R8); \
	PINSRW	$index, (BP)(R8*4), xmm

#define LOAD(off, reg) \
	MOVBLZX	(off*4)(R12),	reg; \
	ADDB	reg,		DX; \
	EXTEND(DX)

#define SKIP(off, reg)

	LOAD(0, AX)
	KEYROUND(X0, LOAD, 0, AX, BX, 0)
	KEYROUND(X1, LOAD, 1, BX, AX, 0)
	KEYROUND(X0, LOAD, 2, AX, BX, 1)
	KEYROUND(X1, LOAD, 3, BX, AX, 1)
	KEYROUND(X0, LOAD, 4, AX, BX, 2)
	KEYROUND(X1, LOAD, 5, BX, AX, 2)
	KEYROUND(X0, LOAD, 6, AX, BX, 3)
	KEYROUND(X1, LOAD, 7, BX, AX, 3)
	KEYROUND(X0, LOAD, 8, AX, BX, 4)
	KEYROUND(X1, LOAD, 9, BX, AX, 4)
	KEYROUND(X0, LOAD, 10, AX, BX, 5)
	KEYROUND(X1, LOAD, 11, BX, AX, 5)
	KEYROUND(X0, LOAD, 12, AX, BX, 6)
	KEYROUND(X1, LOAD, 13, BX, AX, 6)
	KEYROUND(X0, LOAD, 14, AX, BX, 7)
	KEYROUND(X1, SKIP, 15, BX, AX, 7)
	
	ADDB	$16,		CX

	PSLLQ	$8,		X1
	PXOR	X1,		X0
	MOVOU	-16(SI),	X2
	PXOR	X0,		X2
	MOVOU	X2,		-16(DI)

	CMPQ	SI,		R9		  // cmp in with in+len-16
	JLE	start				    // jump if (in <= in+len-16)

end:
	DECB	CX
	ADDQ	$16,		R9		// tmp = in+len

	// handle the last bytes, one by one
l2:	CMPQ	SI,		R9		// cmp in with in+len
	JGE	finished			  // jump if (in >= in+len)

	INCB	CX
	EXTEND(CX)
	MOVBLZX	(BP)(CX*4),	AX

	ADDB	AX,		DX		        // y += tx
	EXTEND(DX)
	MOVBLZX	(BP)(DX*4),	BX		// ty = d[y]
	MOVB	BX,		(BP)(CX*4)	  // d[x] = ty
	ADDB	AX,		BX		        // val = ty+tx
	EXTEND(BX)
	MOVB	AX,		(BP)(DX*4)	  // d[y] = tx
	MOVBLZX	(BP)(BX*4),	R8		// val = d[val]
	XORB	(SI),		R8	      	// xor 1 byte
	MOVB	R8,		(DI)
	INCQ	SI				          // in++
	INCQ	DI			          	// out++
	JMP l2

finished:
	MOVQ	j+40(FP),	BX
	MOVB	DX, 0(BX)
	MOVQ	i+32(FP),	AX
	MOVB	CX, 0(AX)
	RET

```

### RC4 cipher 的使用
首先调用rc4包中的`func NewCipher(key []byte) (*Cipher, error)`新生成一个Cipher, 
  然后调用`func (c *Cipher) XORKeyStream(dst, src []byte)`进行加密或者解密

