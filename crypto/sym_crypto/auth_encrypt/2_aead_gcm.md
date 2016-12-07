# Crypto 学习札记之 Authenticated Encryption 

## 2. AE 算法之 Galois/Counter Mode (GCM)
作为一种authenticated encryption algorithm, [Galois/Counter Mode (GCM)][1] is a mode of operation for symmetric key cryptographic block ciphers.
由于 GCM 效率和性能上的优势 -- 还可以通过硬件资源提升 GCM 的性能，从而实现高速的通信信道，所以大家对它的认可度都比较高😀。

GCM is defined for block ciphers with a block size of 128bits. 

Galois Message Authentication Code (GMAC) is an authentication-only variant of the GCM, which can be used as an incremental message 
authenticaton code.

由于结合了Counter Mode, 所以GCM 和 GMAC 的输入中均包含一个任意长度的 initialization vector.

**性能分析**：

Different block cipher modes of operation can have significantly different performance and efficiency characteristics, even when used 
with the same block cipher. GCM can take full advantage of parallel processing and implementing GCM can make efficient use of an 
instruction pipeline or a hardware pipeline. In contrast, the cipher block chaining mode (CBC mode) of operation incurs significant 
pipeline stalls that hamper its efficiency and performance.

### 2.1  GCM 的基本操作
[GCM][2] 将 counter mode of encryption 与 new Galois mode of authentication 组合起来，基本操作如下图所示，
主要有两大部分：图中的上部分是用于生成密文的 counter mode, 下半部分是用于生成消息认证码MAC的 Galois Mult function (mult_H)

- 对于 counter mode, 这部分还是用于生成密文的
    1. 首先将 blocks 按序编号，然后使用 AES 等 block cipher 加密 block number（这个操作对应E_K), 实际上就是采用AES或者DES对counter进行加密;
    2. 接着再讲加密后的counter_i 与 明文 plaintext_i 做异或操作，得到 ciphertext_i

     注意，counter_0 中应该会结合 initialization value (IV) 的。
- 对于 Galois Mult function, 这部分是用于生成 MAC 的(对应图中的Auth Tag)，从而保证了对于消息的 authentication 和 data integrity 


#### 2.1.1 Additional Authenticated Data
注意，图中初始的Auth Data / additional authenticated data A 就是AEAD中所谓的associated data, 
A 是用来保护那些需要认证但是不能加密的信息的. 当使用 GCM 来确保一个网络协议的安全性时，
A 可以包含网络地址、端口、序列号、协议版本号以及其他表示明文应该如何被handled, forwarded or processed 的信息域. 
当 A 中包含有这些数据的时候， authentication is provided without copying the data into the ciphertext. 
比如TLS协议中的associated data 就是下面四个部分拼接得到的：
1. sequence Number(8 bytes)
2. tls record type (3 bytes)
3. tls version (1 byte) 
4. tls record lenght (1 byte)

#### 2.1.2 Initialization Vector
此外，关于使用 IV 的主要目的在于构成 a nonce, 即对于一个固定的key, 但是每次调用加密操作的结果都是不相同的. 
可以随机生成IV， 只要保证每个key的IV值都是极其不同的。 The IV is authenticated, and it is not necessary to 
include it in the AAD field.

#### 2.1.3 认证能力分析
Both confidentiality and message authentication is provided on the plaintext. The strength of the authentication of
P, IV and A is determined by the length t of the authentication tag. When the length of P is zero, GCM acts as a MAC on 
the input A. The mode of operation that uses GCM as a stand-alone message authentication code is denoted as GMAC.

在具体的一种实现中，生成的tag（MAC）的长度必须是固定的，而且至少得64位，不过最好是128位，因为128位的安全性最高. 
If an IV with a length other than 96 bits is used with a particular key, then that key must be used with a tag length 
of 128 bits.

#### 2.1.4 GCM 中的函数
GCM 中主要用到了两个函数：
1. block cipher encryption, 
    
    The block cipher encryption of the value X with the key K is denoted as E(K, X).
2. multiplication over the field  <img src="http://chart.googleapis.com/chart?cht=tx&chl= \small GF(2^{128})" style="border:none;">. 
    
    其中，
    - $X \cdot Y $  
      : The multiplication of two elements $X,Y \in GF(2^{128}) $ 
    - $X \oplus Y $ 
      : The addition of X and Y. Addition in this field is equivalent to the bitwise exclusive-or operation.

其他的函数，如
- $MSB_{t}(S) $
  : Reuturns the bit string containing only the most significant (leftmost) t bits of S, and the symbol {} denotes
  the bit string with zero length.

### 2.2 GCM 中的加密和解密

#### 2.2.1 GCM 中的加密操作
GCM 的加密操作如下图所示, 图中的 mult_H 操作表示 multiplication in GF(2^128) by the hash key H. 由图可知，
GCM 的加密操作主要由 counter mode of encryption 和 Galois mode of authentication 这两部分组成，
前者是用来加密 plaintext, 属于 stream cipher, 
后者是用来生成 认账码tag (MAC) 的。

此外，authentication 中的GHASH 用到的是有限域 GF(2^128) 上的乘法运算，
而有限域上的乘法运算很容易并行化，
因此相比于其他使用 CBC 模式的authentication algorithms, 其性能更佳。

![GCM basic operation](https://upload.wikimedia.org/wikipedia/commons/6/6a/GCM-Galois_Counter_Mode.svg)

The authneticated encryption is defined by the following equations:
 $$ H = E(K, 0^{128})  $$
> $$ Y_0 = { IV \parallel 0^{32}1 , \  if\ len(IV) = 96, \ else$$
> $$ Y_0 = GHASH(H, \ , IV), \   otherwise.$$

$$ Y_i = incr(Y_{i-1}) \ for\  i = 1, \cdots, n-1$$
$$ C_i = P_i \oplus E(K, Y_i) \ for\  i=1, \cdots, n-1$$
$$ C_n^\ast = P_n^\ast \oplus MSB_u(E(K, Y_n))$$
$$ T = MSB_t(GHASH(H, A, C) \oplus E(K, Y_0))$$

上面的公式中的中间的2、3、4、5 是属于CTR mode 的定义，用来加密明文plaintext 的，
其中用到的符号的含义如下： 
- H 是 hash key, a string of 128 zero bits encrypted using the block cipher (AES/DES)
- Y_0 是利用IV或者GHASH函数生成的初始的计数器，用于CTR mode 中加密明文 plaintext 生成对应的密文 ciphertext 的
- A 是只用于认证（不会被加密）的数据，即AEAD 中的 associated data,
    长度为 <img src="http://chart.googleapis.com/chart?cht=tx&chl= (m-1) \times 128 %2B v" style="border:none;">
- P 是明文 plaintext, 长度为 <img src="http://chart.googleapis.com/chart?cht=tx&chl= (n-1) \times 128 %2B u" style="border:none;">
- C 是密文 ciphertext
- <img src="http://chart.googleapis.com/chart?cht=tx&chl= MSB_t(S)" style="border:none;">:
  reuturns the bit string containing only the most significant (leftmost) t bits of S, and the symbol {} denotes
  the bit string with zero length.

根据上面定义的加密运算，然后使用上面公式中的1、6 即 GHASH 函数生成对应的authentication tag (MAC), 
 GHASH 函数如下, 其中的 additional authenticated data A 和 ciphertext C 是按照上面公式生成的：

![GHASH function](https://wikimedia.org/api/rest_v1/media/math/render/svg/0813d77f30b671f7978ef26b89497f2fde289ca6)

补充：
- H 是 hash key, a string of 128 zero bits encrypted using the block cipher (AES/DES)
- m 是 the number of 128 bit blocks in A, v is the bit length of A_m (the final block of auth data A)
- n 是 the number of 128 bit blocks in C, u is the bit length of C_n (the final block of ciphertext C)
- <img src="http://chart.googleapis.com/chart?cht=tx&chl= \Large \parallel " style="border:none;"> 表示 concatenation 操作

- GHASH 函数中使用到了有限域 <img src="http://chart.googleapis.com/chart?cht=tx&chl=  GF(2^{128})" style="border:none;"> 上的加法和乘法运算，如下：
  - 乘法运算 <img src="http://chart.googleapis.com/chart?cht=tx&chl=  X \cdot Y" style="border:none;">, 即 
    The multiplication of two elements <img src="http://chart.googleapis.com/chart?cht=tx&chl= \small X,Y \in GF(2^{128})" style="border:none;">
  - 加法运算 <img src="http://chart.googleapis.com/chart?cht=tx&chl= X \oplus Y" style="border:none;">, 即
    the addition of X and Y. Addition in this field 等同于按位异或运算. 


#### 2.2.2 GCM 中的解密操作
GCM 的解密操作类似于加密操作，只不过 the hash step 和 encrypt step 的顺序需要倒过来，具体如下：
$$ H = E(K, 0^{128}) $$ 

 <img src="http://chart.googleapis.com/chart?cht=tx&chl= Y_0 = \{ IV \parallel 0^{32}1 , \quad if\quad len(IV) = 96\\ \quad \\ GHASH(H, \{ \quad \}, IV), \quad  otherwise." style="border:none;">

先进行认证，计算出authenticaiton tag T', 判断其是否等于消息中携带的tag T :
$$ T^' = MSB_t(GHASH(H, A, C) \oplus E(K, Y_0)) $$

然后，对密文进行解密：
$$ Y_i = incr(Y_{i-1}) \  for\  i = 1, \cdots, n-1$$
$$ P_i = C_i \oplus E(K, Y_i) \  for\  i=1, \cdots, n-1$$
$$ P_n^\ast = C_n^\ast \oplus MSB_u(E(K, Y_n))$$



### 2.3 GCM 的有限域 GF(2^128)
Anyway，先去补充一下数论中有限域的基础知识吧！😉
数学中的有限域 finite field 亦称为 Galois field, 一个有限域是一个包含有限个元素的集合，该集合上定义了二元运算 -- 乘法运算和加法运算, 
这两种运算需要满足基本的代数运算性质（可交换性 commutativity, 结合律 associativity 以及分配律 distributivity）, 
而运算的结果仍然是有限域中的元素。此外，该有限域中的元素的个数称为该有限域的阶数 order. 对于有限域，其元素的数目必然是素数的幂，而这个对应的素数称为有限域的特征。
另外，所有阶数相同的有限域是同构的，也就是说，从本质上讲，给定有限域的阶，有限域就唯一确定了。

对于一个特定的有限域，其表示是由一个特征多项式决定的。The field polynomial is fixed and determines the representation of the field.
GCM uses the polynomial <img src="http://chart.googleapis.com/chart?cht=tx&chl= f = 1 %2B \alpha %2B \alpha{}^2 %2B \alpha{}^7 %2B \alpha{}^{128}" style="border:none;">


#### 2.3.1 有限域 GF(2^128) 上的乘法运算
有限域 GF(2^128) 上的乘法运算对应的算法表示如下：

---
**Algorithm 1** Multiplication in GF(2^128). Computes the value of 
<img src="http://chart.googleapis.com/chart?cht=tx&chl= Z = X \cdot Y, \mbox{where X, Y and Z} \in GF(2^{128})" style="border:none;">

---
<img src="http://chart.googleapis.com/chart?cht=tx&chl= Z \leftarrow 0, V \leftarrow X" style="border:none;">
```C
for i = 0 to 127 do 
  if Y_i = 1 then 
    Z <—— Z XOR V
  end if
  // 对应 乘法运算： X* alpha^i % 多项式f(alpha^128 + alpha^7 + alpha^2 + alpha + 1) ==> V * alpha % f
  // if 高位 == 0, 则结果是rightshift(V) 
  // if 高位 == 1，则结果是 [ alpha^128 + rightshift(V) ] % f
  //                        == rightshift(V) - (alpha^7 + alpha^2 + alpha + 1) 
  //                        == rightshift(V) + alpha^7 + alpha^2 + alpha + 1
  //                        == rightshift(V) XOR (alpha^7 + alpha^2 + alpha + 1)
  //                        == rightshift(V) XOR R
  if V_127 = 0 then
    V <—— rigtshift(V)
  else
    V <—— rightshift(V) XOR R
  end if
end for
return Z
```
---

上面这个算法中， V runs through the values of 
<img src="http://chart.googleapis.com/chart?cht=tx&chl= X, X \cdot P, X \cdot P^2, \cdots" style="border:none;">, 
and the powers of P correspond to the powers of alpha, modulo the field polynomial f.
This method is identical to Algorithm 1, but is defined in terms of elements instead of bit operations.

提示，这里的X其实可以对应了GCM 加密操作的图中的 mult_H 中的H， 
因此可以先计算出 H % f, H^2 % f, H^3 % f, H^4 % f, ....



#### 2.3.2 计算tag 的 GHASH 函数中的有限域运算
GCM 算法中使用到的有限域 GF(2^128), 即阶数为 <img src="http://chart.googleapis.com/chart?cht=tx&chl= 2^{128} " style="border:none;">
的有限域， 其多项式模运算中的除数使用了如下的多项式：
$$ GF(2^{128}) = x^{128} + x^7 + x^2 + x + 1 $$

换句话说，GCM 算法中的有限域上的乘法运算的key feture 是元素，（对应上面的多项式的系数，除了X^128）：
$$ R = 1110001\parallel 0^{120} $$
其中最左边的位是 X_0, 最右边的位是 X_127

The MAC / authentication tag is constructed by feeding blocks of data into the GHASH function and encrypting the result.
GHASH 函数可以定义为：
$$ GHASH(H, A, C) = X_{m + n + 1}$$

其中，
- H 是 hash key, a string of 128 zero bits encrypted using the block cipher (AES/DES)
- A 是只用于认证（不会被加密）的数据，即AEAD 中的 associated data
- C 是密文ciphertext
- m 是 the number of 128 bit blocks in A, v is the bit length of A_m (the final block of auth data A)
- n 是 the number of 128 bit blocks in C, u is the bit length of C_n (the final block of ciphertext C)
- <img src="http://chart.googleapis.com/chart?cht=tx&chl= \Large \parallel " style="border:none;"> 表示 concatenation 操作
- 变量 X_i, 对于 i=0,...,m+n+1 的定义如下：

![GCM X_i](https://wikimedia.org/api/rest_v1/media/math/render/svg/0813d77f30b671f7978ef26b89497f2fde289ca6)

图中的mult 表示 GF(2^128) 域上的乘法，H 表示用于计算MAC的秘钥， mult H 这表示乘以 GHASH函数中的秘钥H。
此外，值得注意的是，😜 MAC 算法 GHASH 是计算<font color="orange">密文的MAC (不是明文哦😯)</font>的（因此，这属于之前说过的 Authentication Encryption 中的EtM 模式）
则上面的公式表示，

1. 先对于大小约为m个128位分组的 Auth_Data (AEAD 中的 associated data) 做
  <img src="http://chart.googleapis.com/chart?cht=tx&chl= GHASH_H^'(0,\/ authdata\/A) " style="border:none;"> 
 运算（对应上面的公式中的前三条），
其计算结果为的<img src="http://chart.googleapis.com/chart?cht=tx&chl= X_m " style="border:none;">.

    注意，Auth_Data 如果最后一个分组小于128位的话
    （对应第3条公式中的<img src="http://chart.googleapis.com/chart?cht=tx&chl= A^\ast_m \parallel 0^{128-v} " style="border:none;">），
    则需要在后边补0直至凑成128位. 
    因为对于GF(2^128)上的乘法而言，两边的operand 必须都是128位的。

2. 然后对于大小约为n个128位分组的 Ciphertext C 做 
<img src="http://chart.googleapis.com/chart?cht=tx&chl= GHASH_H^'(X_m,\/ ciphertext\/C) " style="border:none;"> 
运算(对应上面的公式中的第4、5条)，
其计算结果为<img src="http://chart.googleapis.com/chart?cht=tx&chl= X_{m%2Bn} " style="border:none;">.

3. 最后再做运算 <img src="http://chart.googleapis.com/chart?cht=tx&chl= GHASH_H^'(X_{m%2Bn},\/ (len(A) \parallel len(C)))" style="border:none;"> ,
 对应上面公式中的最后一条，
 即<img src="http://chart.googleapis.com/chart?cht=tx&chl= (X_{m%2Bn} \oplus (len(A) \parallel len(C))) \cdot H " style="border:none;">,
  最后的计算结果就是用来认证的authentication tag (MAC)

其实总的运算可以表示为，
$$ GHASH_H^'(0,\/ A^' \parallel C^' \parallel len(A) \parallel len(C))   =   GHASH_H^'(0, \/ S) $$ 
$$ = (S_1 \cdot H^{m+n+1}) \oplus (S_2 \cdot H^{m+n}) \oplus \ldots \oplus (S_{m+n+1} \cdot H) $$ 

其中，有两点要说明：
- H表示GHASH函数的秘钥， 0表示初始化的X_0的值，A' 和 C' 则分别表示在A和C右边补0的变种（最后一个分组均要通过补0达到128位😀）;
- 另外，有么有注意到😁，由于GF(2^128)域上的乘法运算的特性，故可以转化成如上面公式的第三部分，
  这样子的话，就可以提前计算出
  <img src="http://chart.googleapis.com/chart?cht=tx&chl=  H^{m%2Bn%2B1},\quad H^{m%2Bn}, \quad \cdots ,\quad H^2, H^1 " style="border:none;">, 
  从而加速MAC的计算。

  
![GCM basic operation](https://upload.wikimedia.org/wikipedia/commons/6/6a/GCM-Galois_Counter_Mode.svg)

### 2.4 Authenticated Encryption 实现
Authenticated Encryption (AE/AEAD) 模式在 go 语言中可以设计为一个接口：
```golang
// AEAD is a cipher mode providing authenticated encryption with associated
// data. For a description of the methodology, see
//	https://en.wikipedia.org/wiki/Authenticated_encryption
type AEAD interface {
	// NonceSize returns the size of the nonce that must be passed to Seal
	// and Open.
	NonceSize() int

	// Overhead returns the maximum difference between the lengths of a
	// plaintext and its ciphertext.
	Overhead() int


  // 对于GCM，
  // 1. 其中的nonce是计数器模式CTR mode 中用于加密plaintext的initialization vector (IV)
  // 2. 而 additionalData 对应上面的authdata, 这个是 GHASH 函数用于计算MAC的.

	// Seal encrypts and authenticates plaintext, authenticates the
	// additional data and appends the result to dst, returning the updated
	// slice. The nonce must be NonceSize() bytes long and unique for all
	// time, for a given key.
	//
	// The plaintext and dst may alias exactly or not at all. To reuse
	// plaintext's storage for the encrypted output, use plaintext[:0] as dst.
	Seal(dst, nonce, plaintext, additionalData []byte) []byte

  // 对于GCM, 
  // 1. CTR mode 中的解密操作需要密文ciphertext和初始化计算器的Nonce (或者说initialization vectro -- IV)
  // 2. 而 验证操作中仍然需要原本的additionaldata，
  //    因为要重新计算GHASH'(0, A || C || len(A) || len(C) ) 得到MAC'，
  //    看看是否等于sender发来的消息中的MAC码，实现验证功能😁

	// Open decrypts and authenticates ciphertext, authenticates the
	// additional data and, if successful, appends the resulting plaintext
	// to dst, returning the updated slice. The nonce must be NonceSize()
	// bytes long and both it and the additional data must match the
	// value passed to Seal.
	//
	// The ciphertext and dst may alias exactly or not at all. To reuse
	// ciphertext's storage for the decrypted output, use ciphertext[:0] as dst.
	//
	// Even if the function fails, the contents of dst, up to its capacity,
	// may be overwritten.
	Open(dst, nonce, ciphertext, additionalData []byte) ([]byte, error)
}

// gcmAble is an interface implemented by ciphers that have a specific optimized
// implementation of GCM, like crypto/aes. NewGCM will check for this interface
// and return the specific AEAD if found.
type gcmAble interface {
	NewGCM(int) (AEAD, error)
}
```


### 2.5 golang cipher包中GCM的实现

golang 的cipher/gcm包实现了GCM，可以调用函数`NewGCM(cipher Block) (AEAD, error)` 或者函数
`func NewGCMWithNonceSize(cipher Block, size int) (AEAD, error)` 来生成接口`AEAD`的实现者`gcm`;
当然，如果某个block cipher 自己实现了GCM（比如block cipher `aes`), 则除了实现接口AEAD中实现的方法外，
还需要实现接口`gcmAble` 中定义的方法`NewGCM(int)(AEAD, error)`，这样子可以有两个好处：
1. 即使不知道对于某个block cipher 的 gcm 的实现方式，用户仍然是使用前面两个函数统一生成新的gcm 
  (有木有觉得使用接口来实现插件式地设计很不错啊，以后偶也要这样子干😉)
2. 但是在调用Seal 和Open 方法的时候，实际上调用的是block cipher 中相应的实现方法。

gcm的定义部分的实现如下, 其中的 `gcm.productTable` 
按照位置顺序

<img src="http://chart.googleapis.com/chart?cht=tx&chl=\Large x_0 , \qquad x_1, \qquad x_2, \cdots , \quad x_{14}, \quad x_{15} " style="border:none;">

存的是：

<img src="http://chart.googleapis.com/chart?cht=tx&chl= 15H , \qquad 14H, \qquad 13H, \qquad \cdots \qquad , \quad H , \quad 0 " style="border:none;">

```golang
// gcmAble is an interface implemented by ciphers that have a specific optimized
// implementation of GCM, like crypto/aes. NewGCM will check for this interface
// and return the specific AEAD if found.
type gcmAble interface {
	NewGCM(int) (AEAD, error)
}

// gcmFieldElement represents a value in GF(2¹²⁸). In order to reflect the GCM
// standard and make getUint64 suitable for marshaling these values, the bits
// are stored backwards. For example:
//   the coefficient of x⁰ can be obtained by v.low >> 63.
//   the coefficient of x⁶³ can be obtained by v.low & 1.
//   the coefficient of x⁶⁴ can be obtained by v.high >> 63.
//   the coefficient of x¹²⁷ can be obtained by v.high & 1.
type gcmFieldElement struct {
	low, high uint64
}

// gcm represents a Galois Counter Mode with a specific key. See
// http://csrc.nist.gov/groups/ST/toolkit/BCM/documents/proposedmodes/gcm/gcm-revised-spec.pdf
type gcm struct {
	cipher    Block
	nonceSize int
	// productTable contains the first sixteen powers of the key, H.
	// However, they are in bit reversed order. See NewGCMWithNonceSize.
	productTable [16]gcmFieldElement
}

// NewGCM returns the given 128-bit, block cipher wrapped in Galois Counter Mode
// with the standard nonce length.
func NewGCM(cipher Block) (AEAD, error) {
	return NewGCMWithNonceSize(cipher, gcmStandardNonceSize)
}

// NewGCMWithNonceSize returns the given 128-bit, block cipher wrapped in Galois
// Counter Mode, which accepts nonces of the given length.
//
// Only use this function if you require compatibility with an existing
// cryptosystem that uses non-standard nonce lengths. All other users should use
// NewGCM, which is faster and more resistant to misuse.
func NewGCMWithNonceSize(cipher Block, size int) (AEAD, error) {
	if cipher, ok := cipher.(gcmAble); ok {
		return cipher.NewGCM(size)
	}

	if cipher.BlockSize() != gcmBlockSize {
		return nil, errors.New("cipher: NewGCM requires 128-bit block cipher")
	}

  // 注意，GHASH_H()函数中的H (下面的key) 其实也是 CTR mode 中的 counter 😂，初始为0
	var key [gcmBlockSize]byte
	cipher.Encrypt(key[:], key[:])

	g := &gcm{cipher: cipher, nonceSize: size}

	// We precompute 16 multiples of |key|. However, when we do lookups
	// into this table we'll be using bits from a field element and
	// therefore the bits will be in the reverse order. So normally one
	// would expect, say, 4*key to be in index 4 of the table but due to
	// this bit ordering it will actually be in index 0010 (base 2) = 2.
	x := gcmFieldElement{
		getUint64(key[:8]),
		getUint64(key[8:]),
	}
	g.productTable[reverseBits(1)] = x

	for i := 2; i < 16; i += 2 {
		g.productTable[reverseBits(i)] = gcmDouble(&g.productTable[reverseBits(i/2)])
		g.productTable[reverseBits(i+1)] = gcmAdd(&g.productTable[reverseBits(i)], &x)
	}

	return g, nil
}

const (
	gcmBlockSize         = 16
	gcmTagSize           = 16
	gcmStandardNonceSize = 12
)

func (g *gcm) NonceSize() int {
	return g.nonceSize
}

func (*gcm) Overhead() int {
	return gcmTagSize
}
```



注意，😞有限域GF(2^n)上定义了加法运算和乘法运算，而关于乘法有一条规则是：
>   如果乘法运算的结果是次数大于 n-1 的多项式，
   那么必须除以某个次数为n 的irreducible polynomial 并取其余数

而 GCM 中用到的用于约减的多项式是 

<img src="http://chart.googleapis.com/chart?cht=tx&chl=\Large GF(2^{128}) = x^{128} %2B x^7 %2B x^2 %2B x %2B 1" style="border:none;">

因此，当最高位原本是1的话 -- 2^127，乘以2的结果必然超出(最高项变为2^127 * 2 = 2^128)
然后除以GCM中定义的多项式的话，最高位直接弃掉就行了, 剩下的部分做subsraction 运算即可，
而对于2上的减法运算， 实际上等于加法运算，而 addition == XOR, 所以转变为异或运算

也就是说，只要异或上1 + x + x^2 + x^7 表示的集合 0000 0000... 0000 0000 1110 0001 就可以了
而double.high 部分异或的是0，所以double.high 不变，只要对double.low做异或操作即可。
但是，又因为x.low 表示的顺序是 x_0 x_1 x_2 x_3 x_4 ... x_63, 所以需要将 0000 0000... 0000 0000 1110 0001 进行转置，再跟double.low 进行异或
所以，最终就是 double.low ^= 0xe100000000000000


```golang
// reverseBits reverses the order of the bits of 4-bit number in i.
func reverseBits(i int) int {
	i = ((i << 2) & 0xc) | ((i >> 2) & 0x3)
	i = ((i << 1) & 0xa) | ((i >> 1) & 0x5)
	return i
}

// gcmAdd adds two elements of GF(2¹²⁸) and returns the sum.
func gcmAdd(x, y *gcmFieldElement) gcmFieldElement {
	// Addition in a characteristic 2 field is just XOR.
	return gcmFieldElement{x.low ^ y.low, x.high ^ y.high}
}

// gcmDouble returns the result of doubling an element of GF(2¹²⁸).
func gcmDouble(x *gcmFieldElement) (double gcmFieldElement) {
	msbSet := x.high&1 == 1

	// Because of the bit-ordering, doubling is actually a right shift.
	double.high = x.high >> 1
	double.high |= x.low << 63
	double.low = x.low >> 1

	// If the most-significant bit was set before shifting then it,
	// conceptually, becomes a term of x^128. This is greater than the
	// irreducible polynomial so the result has to be reduced. The
	// irreducible polynomial is 1+x+x^2+x^7+x^128. We can subtract that to
	// eliminate the term at x^128 which also means subtracting the other
	// four terms. In characteristic 2 fields, subtraction == addition ==
	// XOR.
	if msbSet {
		double.low ^= 0xe100000000000000
	}

	return
}
```


说明：

Block是代表 block cipher 的一个接口，如下
```golang
// A Block represents an implementation of block cipher
// using a given key. It provides the capability to encrypt
// or decrypt individual blocks. The mode implementations
// extend that capability to streams of blocks.
type Block interface {
	// BlockSize returns the cipher's block size.
	BlockSize() int

	// Encrypt encrypts the first block in src into dst.
	// Dst and src may point at the same memory.
	Encrypt(dst, src []byte)

	// Decrypt decrypts the first block in src into dst.
	// Dst and src may point at the same memory.
	Decrypt(dst, src []byte)
}

```

其中，go的cipher包下的gcm.go中的`gcm`实现了该接口，下面是`Seal`方法的定义：
```golang
func (g *gcm) Seal(dst, nonce, plaintext, data []byte) []byte {
	if len(nonce) != g.nonceSize {
		panic("cipher: incorrect nonce length given to GCM")
	}
	ret, out := sliceForAppend(dst, len(plaintext)+gcmTagSize)

	var counter, tagMask [gcmBlockSize]byte
	g.deriveCounter(&counter, nonce)

	g.cipher.Encrypt(tagMask[:], counter[:])
	gcmInc32(&counter)

	g.counterCrypt(out, plaintext, &counter)
	g.auth(out[len(plaintext):], out[:len(plaintext)], data, &tagMask)

	return ret
}
```
下面是解密方法`Open`的实现：
```golang
var errOpen = errors.New("cipher: message authentication failed")

func (g *gcm) Open(dst, nonce, ciphertext, data []byte) ([]byte, error) {
	if len(nonce) != g.nonceSize {
		panic("cipher: incorrect nonce length given to GCM")
	}

	if len(ciphertext) < gcmTagSize {
		return nil, errOpen
	}
	tag := ciphertext[len(ciphertext)-gcmTagSize:]
	ciphertext = ciphertext[:len(ciphertext)-gcmTagSize]

	var counter, tagMask [gcmBlockSize]byte
	g.deriveCounter(&counter, nonce)

	g.cipher.Encrypt(tagMask[:], counter[:])
	gcmInc32(&counter)

	var expectedTag [gcmTagSize]byte
	g.auth(expectedTag[:], ciphertext, data, &tagMask)

	ret, out := sliceForAppend(dst, len(ciphertext))

	if subtle.ConstantTimeCompare(expectedTag[:], tag) != 1 {
		// The AESNI code decrypts and authenticates concurrently, and
		// so overwrites dst in the event of a tag mismatch. That
		// behaviour is mimicked here in order to be consistent across
		// platforms.
		for i := range out {
			out[i] = 0
		}
		return nil, errOpen
	}

	g.counterCrypt(out, ciphertext, &counter)

	return ret, nil
}
```

### 2.6 GCM 在TLS中的应用
在TLS协议的实现中就使用AEAD，使用例子如下, 其中， tls record protocol中的additionalData (对应AEAD中的associated data)  主要包含如下四部分：
1. sequence Number(8 bytes)
2. tls record type (3 bytes)
3. tls version (1 byte) 
4. tls record lenght (1 byte)

```golang
//加密部分
// encrypt encrypts and macs the data in b.
func (hc *halfConn) encrypt(b *block, explicitIVLen int) (bool, alert) {
	// mac
	if hc.mac != nil {
		mac := hc.mac.MAC(hc.outDigestBuf, hc.seq[0:], b.data[:recordHeaderLen], b.data[recordHeaderLen+explicitIVLen:])

		n := len(b.data)
		b.resize(n + len(mac))
		copy(b.data[n:], mac)
		hc.outDigestBuf = mac
	}

	payload := b.data[recordHeaderLen:]

	// encrypt
	if hc.cipher != nil {
		switch c := hc.cipher.(type) {
		case cipher.Stream:
			c.XORKeyStream(payload, payload)
		case cipher.AEAD:
			payloadLen := len(b.data) - recordHeaderLen - explicitIVLen
			b.resize(len(b.data) + c.Overhead())
			nonce := b.data[recordHeaderLen : recordHeaderLen+explicitIVLen]
			payload := b.data[recordHeaderLen+explicitIVLen:]
			payload = payload[:payloadLen]

			copy(hc.additionalData[:], hc.seq[:])
			copy(hc.additionalData[8:], b.data[:3])
			hc.additionalData[11] = byte(payloadLen >> 8)
			hc.additionalData[12] = byte(payloadLen)

			c.Seal(payload[:0], nonce, payload, hc.additionalData[:])
		case cbcMode:
      // ...
				default:
			panic("unknown cipher type")
		}
	}

	// update length to include MAC and any block padding needed.
	n := len(b.data) - recordHeaderLen
	b.data[3] = byte(n >> 8)
	b.data[4] = byte(n)
	hc.incSeq()

	return true, 0
}

//解密部分
// decrypt checks and strips the mac and decrypts the data in b. Returns a
// success boolean, the number of bytes to skip from the start of the record in
// order to get the application payload, and an optional alert value.
func (hc *halfConn) decrypt(b *block) (ok bool, prefixLen int, alertValue alert) {
	// pull out payload
	payload := b.data[recordHeaderLen:]

	macSize := 0
	if hc.mac != nil {
		macSize = hc.mac.Size()
	}

	paddingGood := byte(255)
	explicitIVLen := 0

	// decrypt
	if hc.cipher != nil {
		switch c := hc.cipher.(type) {
		case cipher.Stream:
			c.XORKeyStream(payload, payload)
		case cipher.AEAD:
			explicitIVLen = 8
			if len(payload) < explicitIVLen {
				return false, 0, alertBadRecordMAC
			}
			nonce := payload[:8]
			payload = payload[8:]

			copy(hc.additionalData[:], hc.seq[:])
			copy(hc.additionalData[8:], b.data[:3])
			n := len(payload) - c.Overhead()
			hc.additionalData[11] = byte(n >> 8)
			hc.additionalData[12] = byte(n)
			var err error
			payload, err = c.Open(payload[:0], nonce, payload, hc.additionalData[:])
			if err != nil {
				return false, 0, alertBadRecordMAC
			}
			b.resize(recordHeaderLen + explicitIVLen + len(payload))
		case cbcMode:
        // ...

		default:
			panic("unknown cipher type")
		}
	}

	// check, strip mac
	if hc.mac != nil {
		if len(payload) < macSize {
			return false, 0, alertBadRecordMAC
		}

		// strip mac off payload, b.data
		n := len(payload) - macSize
		b.data[3] = byte(n >> 8)
		b.data[4] = byte(n)
		b.resize(recordHeaderLen + explicitIVLen + n)
		remoteMAC := payload[n:]
		localMAC := hc.mac.MAC(hc.inDigestBuf, hc.seq[0:], b.data[:recordHeaderLen], payload[:n])

		if subtle.ConstantTimeCompare(localMAC, remoteMAC) != 1 || paddingGood != 255 {
			return false, 0, alertBadRecordMAC
		}
		hc.inDigestBuf = localMAC
	}
	hc.incSeq()

	return true, recordHeaderLen + explicitIVLen, 0
}
```


## 资料汇总
1. NIST GCM : http://csrc.nist.gov/groups/ST/toolkit/BCM/documents/proposedmodes/gcm/gcm-revised-spec.pdf

[1]: https://en.wikipedia.org/wiki/Galois/Counter_Mode "Galois Counter Mode"
[2]: http://csrc.nist.gov/groups/ST/toolkit/BCM/documents/proposedmodes/gcm/gcm-revised-spec.pdf "GCM Specification"
