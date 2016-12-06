# Crypto 学习札记之 Operation Modes of Block Cipher
密码学中，a <b>mode of operation</b> 是一个使用[block cipher](https://en.wikipedia.org/wiki/Block_cipher)
来提供confidentiality 或者 authenticity 服务的。block cipher 自身只适合对于一个固定长度的块进行加密或者解密操作，
而 a mode of operation 提供了如何重复地将一个cipher的单个块操作转化为适应大量的数据（包含多个块）。
因此，对于变长的消息，它需要先划分为固定长度的blocks, 应用block cipher中的加密操作，生成cipher blocks, 然后再结合
某种连接模式，将这些cipher blocks连接起来，生成最终的密文。

常见的[block cipher mode of operation](https://en.wikipedia.org/wiki/Block_cipher_mode_of_operation) 有：

1. Electornic Codebook (ECB)，
  最简单的mode, 对于加密，The message is divided into blocks, and each block is encrypted separately. 然后再把各个密文块连接起来。
  注意到各个块之间的加密是互不影响的，因此，对于相同的plaintext，它是会生成同样的ciphertext的。因此，虽然它简单，但是会引发两个缺点：
   - 对于bitmaps, 加密后的位图可能会看得出原本的位图的模式
   - 对于协议，如果使用了ECB模式，那么协议就不会有完整性保护，由于每个块都是使用完全一样的方式进行加密，那么协议更容易受到replay attacks.

2. Cipher Block Chaining (CBC)
  而对于CBC模式，它把前一块密文与当前待加密的block进行异或操作，从而使得下一密文块的生成依赖于前面的所有处理过的blocks。而对于第一个密文块
  的生成，它是通过第一个明文块与一个随机的iv生成的(block_1 xor initialization_vector)，这样子变保证了整体密文生成的随机性
  （对于同样的明文和block cipher -- key）. 如果不知道IV的话，解密操作对于除了第一块的其它blocks是可以并行解密的，因此如果在明文的前面
  添加一个随机的block 作为 Explicit Initialization Vectors (TLS 协议中)的话，那么就可以实现对所有的密文块的并行解密操作。BTW, CBC 模式是应用
  最广泛的😄。

3. Propagating Cipher Block Chaining (PCBC)
  亦称为plaintext cipher block chaining, 在此种模式中，each block of plaintext is XORed with
  both the previous plaintext block and the previous ciphertext block before being encrypted. 
  注意，相比于CBC，它的异或操作除了跟前一个密文块异或外，还会跟前一个明文快进行亦或操作。
  Kerberos计算机网络认证协议以及WASTE协议中都用到了PCBC模式。

4. Cipher Feedback (CFB)
  注意与CBC的区别，CBC加密操作中，是使用明文块P_i与前一个密文块C_{i-1}异或之后再进行加密E_K得到密文块C_i的，
  而CFB的加密操作却是，先对前一个密文块C_{i-1}进行加密操作E_K, 然后再与明文块P_i进行亦或操作，从而生成密文块C_i的，
  天呐，有木有觉得很类似😏。
  这样子的话，CFB的解密操作应该是先将密文块C_{i-1}进行加密操作E_K, 然后再与密文块C_i进行异或操作，便可以得到对应的明文块P_i了。

5. Output Feedback (OFB)
  OFB 模式
6. Counter (CTR)

**关于IV**

Initialization vector (IV), 是各个模式中用来初始化加密操作的变量，IV必须得随机点，这样子的话，即使block cipher 使用了同样的key，
即使是同一个plaintext, 那么最终经过模式中的连接以及block cipher 的加密操作后，生成的密文也是不同的。

**关于padding**

另外，必须得注意，与mode结合使用的block cipher，按照传统，如果是当成block cipher来使用的话，即是对明文进行进行fixed-size分组，
故通常最后一块需要padding to fixed size; 但是如果把block cipher 当成stream cipher来使用（即不对明文进行分组），则不需要打补丁。

## 1. Block Cipher 与 Block Mode
密码学中，a <b>block cipher</b> 是一个针对固定长度的block进行加密或者解密的deterministic algorithm，其中加密或者解密是由一个对称密钥决定的。
Block ciphers 是密码学协议中的基本组件。而Block Mode 则定义了将大的message进行切分成blocks，结合Block cipher对于单个block的加密与解密，选择某种
方式将这些blocks链接成最终的密文或者明文。

一个block cipher包含两个配对的算法，一个是加密算法E，另外一个是解密算法D, 解密算法可以定义为加密的转置函数。
两个算法的输入均有两个，一个是大小为n位的block，另外一个是大小为k为的key; 算法的输出均为大小为n位的block. 

Block cipher的加密函数可以定义如下：

$$ E_k(P) := E(P, K) : \{0, 1\}^n \times \{0, 1\}^k \rightarrow \{0, 1\}^n $$
解密可以定义如下：

$$ E_k^{-1}(C) := D(C, K) : \{0, 1\}^n \times \{0, 1\}^k \rightarrow \{0, 1\}^n $$

其中，P表示大小为n位的plaintext（即明文块）,  C表示大小为n位的ciphertext（即加密后的密文块）, 而K表示大小为k位的key, 
对于任意的key K, 对密文ciphertext C进行解密操作后会得到原本的明文plaintext， 可以表示如下：

$$ \forall{K} : D_K(E_K(P)) = P $$

### 1.1 Block Cipher 实现
可以将Block cipher 定义成接口，如下
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
### 1.2 Block Mode的实现

block cipher mode of operation 可以定义为统一的接口，其中的`CryptBlocks`既可以是加密亦可以是解密操作，
如下：
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

