# Message Authentication Code

## 1. MAC 定义
密码学中， a <font color="red"> message authentication code (MAC)</font> 是用来authenticate a message 的数据。
认证一个message只要有两方面的认证：
- message's authenticity: 确认消息是否真的是由the stated sender 发送的；
- message's integrity: 确认消息是否在发送的过程中有改变

a MAC algorithm, 有时候叫做 a keyed (cryptographic) hash function 
(实际上， a cryptographic hash function 只是众多用来生成MAC的方式中的一种而已) ,
该函数的输入输出如下：
- input: a secret key, an arbitrary-length message to be authenticated
- output: a MAC (亦称为 *tag*).

因此，verifiers 只要拥有the secret key 就可以确认消息 的authenticity 以及数据完整性。

MAC 包含了如下三种算法：
1. 秘钥生成算法： selects a ey from the key space uniformly at random.
2. 签名算法：returns a tag given the key and the message.
3. 验证算法：verifies the authenticity of the message given the key and the tag. 

又可以定义为满足如下条件的三元组算法（G, S, V)， 其中：
1. G (key-generator) gives the key k on input 1^n, 其中 n 是安全参数；
2. S (Signing) outputs a tag t on the key k and the input string x;
3. V (Verifying) outputs acceppted or rejected on inputs: 
    the key k, the string x and the tag t.
     而 S 和 V 必须满足 <img src="http://chart.googleapis.com/chart?cht=tx&chl= Pr[k \leftarrow G(1^n), V(k, x, S(k, x)) = accepted]" style="border:none;">


MAC 的示意图如下：

![MAC Algorithm 示例](https://upload.wikimedia.org/wikipedia/commons/0/08/MAC.svg)


### 1.1 MACs vs digital signatures

MACs 与 数字签名的不同点在于，生成和验证 MAC values 用的都是相同的secret key，而数字签名属于public-key cryptography, 它是使用私钥生成、公钥验证的。
由于MAC 值的生成和验证采用的都是相同的secret key, 因此消息的发送者与接收者必须在发起通信前需要agree on the same key, 
这点跟symmetric encryption 是相同的。

### 1.2 MACs vs Cryptographic Hash Function
MACs 可以使用cryptographic hash function 来实现，亦可以使用普通的哈希函数或者block cipher 等方式来实现；

Cryptographic Hash Function 是诸多哈希函数中满足特定属性从而应用于cryptography的一类。
它的输入称为<font color="red"> message </font>, 输出称为<font color="red"> message digest ( digest or hash )</font> 
跟其他哈希函数一样，它都是将任意长度的输入转化为固定长度的输出，但除此之外，它还必须满足如下特性：
1. 快：对于任意长度的message, 要能快速计算出对应的哈希值（也称为 message digest） 
2. 不可逆转性：infeasible to generate a message from its hash value， 除非通过尝试所有可能的消息
3. 蝴蝶效应：a small change to a message should change change the hash value so extensively that 
    the new hash value appears uncroorelated with the old hash value
4. 不可重复性：infeasible to find two different message with the same hash value


#### 1.2.1 Cryptograhpic hash functions 的应用
Cryptographic hash functions 在信息安全中应用广泛，比如 digital signatures, message authentication codes (MACs), and other forms of authentication.
当然，cryptographic hash functions 也可以当成普通的哈希函数来用，即
- to index data in hash tables;
- for fingerprinting, to detect duplicate or uniquely identify files;
- as checksums to detect accidental corruption.

更加严格来说，cryptographic hash functions 有如下应用：
1. Verifying the integrity of files or messages, 
  因为cryptographic hash functions 对于输入哪怕一个比特位的改变，生成的消息摘要都是完全不同的。
  这也使得数字签名算法可以只对这类哈希函数生成的消息摘要计算签名。
2. Password verification, 可以利用这类函数计算出每个 password 的 hash digest, 然后存储到数据库中，这样就可以减少存储明文密码带来的风险了。
    不过在实际中，通常还会将password 连接上 a random, non-secet <font color="red">salt</font> ，然后存储的是 hash(password_salt)，
    因为对于不同的用户，其 password 是不一样的，因此可以进一步降低通过提前计算出常见的密码的哈希值来盗取用户的账户。
3. Proof-of-work, [proof-or-work system][1] (or protocol, or function) 
     require some work from service requester (通常是指服务请求者需要耗费一定的处理时间)  ，
     从而可以抵制 denial of service attacks 和其他的service abuses such as spam o a network 的。
     工作量证明机制中有一个明显的“不公平”😉的特性，
      - 对于服务请求者来说，the work must be moderately hard (but feasible); 
      - 但是对于服务提供者来说，the work is easy to check

    Bitcoin mining 和 Hashcash 就使用了工作量证明机制，它采用了partial hash inversions 来prove that the work was done，
    从而保证了挖矿者向节点发布的请求合并它生成的区块的消息不是什么垃圾消息😄。
    具体来说，
      - 挖矿者要干的工作是：通过改变消息中的一个计数器nonce的值，然后使用 cryptographic hash function 来计算出整个消息的哈希值，使得该 hash value begins with a number of zero bits. 其工作的难度取决于要求哈希值前缀中的0的位数，
        因为the number of zero bits 要求地越多，那么找到一个满足该要求的哈希值的工作量也会指数式增加。然后把该nonce 附带到消息中发送给peer节点
      - 而对于服务提供者（peer 节点）来说，接收到该消息后，验证工作非常地容易，只要计算出消息的哈希值，然后判断该哈希值的开头是否有足够多的0就可以了
      （真的好不公平，有木有😒）

4. File or data identifier，这个是将 message digest 当做标识文件的工具，此种用法也是利用了cryptographic hash functions 对于不同的输入（file or data），生成的哈希值都是不一样的，因此可以作为
    file 或者 data 的指纹 fingerprint. 忽然想起了之前写的重复数据删除文件系统😄，当时就是使用文件的MD5值作为文件的指纹的；
    此外，Git, Mercurial 等源码管理系统利用SHA1计算文件内容、目录树等不同类型的信息对应的哈希值作为标记这些信息的指纹。
5. Pseudorandom generation and key derivation


## 2. MAC 实现
1. 利用其它cryptographic primitives 来构造 MAC 算法：
    - 利用cryptographic hash functions: The Keyed-Hash Message Authentication Code (HMAC)
    - 利用block cipher algorithms: OMAC, CBC-MAC, PMAC
2. 利用 universal hashing: UMAC, VMAC
3. 也可以组合多种cryptographic primitives， 比如TLS 中，输入的数据被分成两组，
  每组都使用不同的hashing primitive (MD5, SHA-1) 得到不同的哈希值，
  然后两个哈希值再异或，异或的结果就是MAC


## 3. MAC 算法 之 Hash-based message authentication code (HMAC)
密码学中， a keyed-hash message authentication code (HMAC) 是MAC的一种具体实现类型，同样提供了MAC 对于认证消息的两个功能：
- authentication of a message
- data integrity

HMAC 涉及到两部分：
1. a cryptographic hash function, 比如 MD5、SHA-1，该函数是用来计算HMAC的，
  对应的 MAC 算法分别称为 HMAC-MD5、HMAC-SHA1, IPsec 和 TLS protocols 就用到了这两种 HMAC 算法。
  因此，生成的 HMAC 的位数取决于所使用的cryptographic hash function 生成的哈希值的位数。
2. a secret cryptographic key

HMAC 的cryptographic strength 主要取决于所使用的哈希函数的cryptographic strenth, 生成的哈希值的位数，以及key 的位数和质量。

### 3.1 HMAC 的定义
HMAC算法可以定义为：

<img src="http://chart.googleapis.com/chart?cht=tx&chl= HMAC(K, m) = H(\/ (K^' \oplus opad) \parallel H((K^' \oplus ipad) \parallel m)\/ )" style="border:none;">

其中，
- H : a cryptographic hash function
- K : the secret key
- m : the message to be authenticated
- <img src="http://chart.googleapis.com/chart?cht=tx&chl= K^' " style="border:none;"> : 是从原本的key K 得到的， 具体有两种情况:
    - 如果`len( key K ) < blocksize` ，则需要 by padding K to the right with extra zeros to the input block size of the hash function,
      即在K的右边补0，直到key的长度等于块的大小。
    - 如果`len( key K ) > blocksize` ， 则学哟啊 by hashing K if it is longer than that block size 
      (blocksize == cryptographic hash function 生成的hash digest的大小)
- <img src="http://chart.googleapis.com/chart?cht=tx&chl= \parallel ' " style="border:none;"> 表示concatenation
- opad: the outer padding (0x5c5c5c...5c5c), 是一个 one-block-long hexadecimal constant
- ipad: the inner padding (0x363636...3636), 也是一个 长度为one-block 的 hexadecimal constant

### 3.2 HMAC 的实现
根据上面HMAC 的定义，可以实现如下, 注意用户在生成一个新的HMAC 哈希的时候，
需要在函数`func New(h func() hash.Hash(), key []byte) hash.Hash` 中指定HMAC 所需要用的cryptographic hash function 和 secret key,
  当然，第一个参数是一个函数，需要将cryptographic hash function 包装一下。
具体的HMAC 实现见下面的代码, 注意
- 对于sender, 只需要前3个步骤计算出MAC就可以了，
- 而对于receiver, 除了使用前三个步骤计算出MAC，还需要步骤4验证MAC是否相同，从而对消息的authentication 以及 数据的完整性进行核实。

```golang
// FIPS 198-1:
// http://csrc.nist.gov/publications/fips/fips198-1/FIPS-198-1_final.pdf

// key is zero padded to the block size of the hash function
// ipad = 0x36 byte repeated for key length
// opad = 0x5c byte repeated for key length
// hmac = H([key ^ opad] H([key ^ ipad] text))

type hmac struct {
	size         int
	blocksize    int
	opad, ipad   []byte
	outer, inner hash.Hash
}

// 3. 最后再统一调用 Sum(nil) 即可返回认证码 MAC
func (h *hmac) Sum(in []byte) []byte {
	origLen := len(in)
	in = h.inner.Sum(in)
	h.outer.Reset()
	h.outer.Write(h.opad)
	h.outer.Write(in[origLen:])
	return h.outer.Sum(in[:origLen])
}

// 2. 然后往HMAC hash 写入 message m, 这部分的操作对应内部的Hash( （ipad xor k^')_message )
func (h *hmac) Write(p []byte) (n int, err error) {
	return h.inner.Write(p)
}

func (h *hmac) Size() int { return h.size }

func (h *hmac) BlockSize() int { return h.blocksize }

func (h *hmac) Reset() {
	h.inner.Reset()
	h.inner.Write(h.ipad)
}

// 1. 使用的时候，先New 一个 HMAC hash
// New returns a new HMAC hash using the given hash.Hash type and key.
func New(h func() hash.Hash, key []byte) hash.Hash {
	hm := new(hmac)
	hm.outer = h()
	hm.inner = h()
	hm.size = hm.inner.Size()
	hm.blocksize = hm.inner.BlockSize()
	hm.ipad = make([]byte, hm.blocksize)
	hm.opad = make([]byte, hm.blocksize)
	if len(key) > hm.blocksize {
		// If key is too big, hash it.
		hm.outer.Write(key)
		key = hm.outer.Sum(nil)
	}
	copy(hm.ipad, key)
	copy(hm.opad, key)
	for i := range hm.ipad {
		hm.ipad[i] ^= 0x36
	}
	for i := range hm.opad {
		hm.opad[i] ^= 0x5c
	}
	hm.inner.Write(hm.ipad)
	return hm
}

//[4]. 对于receiver -- MAC 的验证, 除了前面的3个步骤(重新计算消息的MAC码), 
// 还需要再调用该函数比较sender发来的消息中的MAC 与receiver 自己生成的MAC是否相同。
// Equal compares two MACs for equality without leaking timing information.
func Equal(mac1, mac2 []byte) bool {
	// We don't have to be constant time if the lengths of the MACs are
	// different as that suggests that a completely different hash function
	// was used.
	return len(mac1) == len(mac2) && subtle.ConstantTimeCompare(mac1, mac2) == 1
}
```

注意，上面的 `hmac` 实现了 `hash.Hash`接口，该接口定义的方法如下：
```golang
// Hash is the common interface implemented by all hash functions.
type Hash interface {
	// Write (via the embedded io.Writer interface) adds more data to the running hash.
	// It never returns an error.
	io.Writer

	// Sum appends the current hash to b and returns the resulting slice.
	// It does not change the underlying hash state.
	Sum(b []byte) []byte

	// Reset resets the Hash to its initial state.
	Reset()

	// Size returns the number of bytes Sum will return.
	Size() int

	// BlockSize returns the hash's underlying block size.
	// The Write method must be able to accept any amount
	// of data, but it may operate more efficiently if all writes
	// are a multiple of the block size.
	BlockSize() int
}

```

其中内嵌的 `io.Writer` 接口的定义如下, 对于`hmac`而言，其实就是将消息`p []byte`
```golang
// Writer is the interface that wraps the basic Write method.
//
// Write writes len(p) bytes from p to the underlying data stream.
// It returns the number of bytes written from p (0 <= n <= len(p))
// and any error encountered that caused the write to stop early.
// Write must return a non-nil error if it returns n < len(p).
// Write must not modify the slice data, even temporarily.
//
// Implementations must not retain p.
type Writer interface {
	Write(p []byte) (n int, err error)
}

```

[1]: https://en.wikipedia.org/wiki/Proof-of-work_system "Proof of Work System"
