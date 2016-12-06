# Block cipher 学习札记之 DES

## DES 的架构

DES 由 IP、16轮转换运算、FP 这三种操作组成，如下图所示。

1. IP: 首先，在第一轮开始前，the blocks 被分成两个32位分组，然后分别交替处理；
2. Transformation rounds: 图中的交叉线表示 Feistel Scheme, Feistel Structure 可以保证加密和解密的过程比较类似，
  唯一的不同点在于 the subkeys are applied in the reverse order when decrypting.
  中间的16轮都是相同的过程😂
3. FP: 最后再将两个32位分组转换为计算机硬件存储中以字节为单位的类型--8个bytes

注意，图中的IP、FP的具体的置换规则可以参看[此材料中的 Initial permutation (IP) 和 Final permutation (FP)](https://en.wikipedia.org/wiki/DES_supplementary_material),
IP 的实现代码可以见[DES 实现之 Initial Permutation](#imp_ip),
FP 的实现代码可以见[DES 实现之 Final Permutation](#imp_fp)

对于中间的转换操作，进一步解释：
- 图中的 <img src="http://chart.googleapis.com/chart?cht=tx&chl= \oplus " style="border:none;"> 表示异或操作；
- F-function scramble half a block together with some of the key. The output from the F-function is then combined with the other half of the block,
  and the halves are swapped before the next round. After the final round, the halfves are swapped; 
  this is a feature of the Feistel strucure which makes ecryption and decryption similar processes.

<img caption="The overall Feistel structure of DES" width="40%" align="middle" src="https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/DES-main-network.png/500px-DES-main-network.png">


### <label id="sub_feistelfunc">The Feistel (F) function</label>
The F-function, 每次作用于半个分组上(32 bits) ，总共有四个阶段，如下图所示：

1. Expansion: 使用 expansion permutation(对应图中的 E) 将32位的half-block 转换为48位. 具体为duplicate half of the bits. 输出为 eight 6-bit (8\*6=48 bits) pieces, 
   each containing a copy of 4 corresponding input bits, plus a copy of the immediately adjacent bit from each of the input pieces to either side.
   具体的扩展规则见[此材料中的 Expansion function (E)](https://en.wikipedia.org/wiki/DES_supplementary_material)
2. Key mixing: 上一步的48位输出跟一个48位的subkey 做异或操作。 注意16轮中都有一个subkey, 这些subkeys 均是对 the main key 使用 key schedule 生成的。
3. Substitution: 跟subkey 做完异或操作后， the block is divided into eight 6-bit pieces before processing by the S-boxes, or substitution boxes. 
   每个S-boxes 都是根据 lookup table 中的肥西那行转换将 the <b>six</b> input bits 转换为 the <b>four</b> ouput bits. 
   S-boxes 保障了 DES 的安全性. 
   8个S-boxes的替换规则可以参看[此材料中的 Substitution boxes (S-boxes)](https://en.wikipedia.org/wiki/DES_supplementary_material), 
   其实这个相当于古典密码中的8\*单表替代密码😂
4. Permutation: 上一步的8个 S-boxes 输出是32 bits. The 32 outputs from the S-boxes are rearranged according to a fixed permutation, the P-box. T
    his is designed so that, after permutation, each S-box's output bits are spread across four different S boxes in the next round.
    具体的置换规则的定义可以参看[此材料中的Permution (P) 下的表](https://en.wikipedia.org/wiki/DES_supplementary_material)，赤裸裸的置换（说实话就是打乱顺序重新排列了一下😂）

看到这里，有没有觉得DES 其实就是替换substitution 和 置换 permutation 的组成啊，本质上并没有啥创新的😂

![The Feistel function (F-function) of DES](https://upload.wikimedia.org/wikipedia/commons/thumb/2/25/Data_Encription_Standard_Flow_Diagram.svg/500px-Data_Encription_Standard_Flow_Diagram.svg.png)

Feistel Function 的实现代码可见<a href="#imp_feistelfunc">这里</a>

### <label id= sec_keyschedule>Key schedule</label>
上面提到了DES 加密过程中的16轮转换操作中用到的subkeys 是对 the main key 应用 Key schedule 生成的，该算法如下图所示，
实现可以参看<a href="#imp_keyschedule"> DES 中 subkey 的实现</a>
1. 首先， 使用 Permutated Choice 1 (PC-1) 从原本64位的 key 中选出56位，剩下的8位弃置或者当成 parity check bits 使用。
2. 然后，将上面选出的56位key 分成两半，每一部分28位。Each half is thereafter treated separately. 
3. 在接下来的16个rounds 中，每一部分都会先循环左移一位或者两位（具体左移的位数由具体的round 决定，对应图中的 <<< 符号）。
    And then 48 subkey bits are selectted by Permuted Choice 2 (PC-2) -- 24 bits from the left half, and 24 from the right. 

另外，解密过程中的 key schedule 也是类似于上面的步骤的，只不过与用于加密的 key schedule 相比，它生成的subkeys 顺序正好颠倒过来。
图中的PC1 和 PC2 操作中用到的置换表见
[DES 补充材料中的 Permuted choice 1 (PC-1) 和 Permuted choice 2 (PC-2)](https://en.wikipedia.org/wiki/DES_supplementary_material)，
特别注意到PC-1中只用到了56位，其中的bit 8, 16, 24, 32, 40, 48, 56, 64 这8 ibts 是用于奇偶校验码的😇

![ The key-schedule of DES](https://upload.wikimedia.org/wikipedia/commons/0/06/DES-key-schedule.png)


### DES 的使用与实现

#### DES 的使用
golang 中的crypto/des包已经实现了DES 算法了，调用的接口如下, 
1. 首先调用`NewCipher(key []byte) (cipher.Block, error)`函数生成一个cipher.Block， 需要传入一个64位的key (前面说过了其中的8位是用于parity checking的)
2. 然后调用`Encrypt(dst, src []byte)` 进行加密明文src, 生成密文dst
3. 若是解密，则调用`Decrypt(dst, src []byte)` 解密密文src, 生成明文dst

此外， Block Cipher DES 中所处理的分组的大小是64位（8个字节），调用`BlockSize() int` 即可以返回分组大小

```golang
// The DES block size in bytes.
const BlockSize = 8

type KeySizeError int

func (k KeySizeError) Error() string {
	return "crypto/des: invalid key size " + strconv.Itoa(int(k))
}

// desCipher is an instance of DES encryption.
type desCipher struct {
	subkeys [16]uint64
}

// NewCipher creates and returns a new cipher.Block.
func NewCipher(key []byte) (cipher.Block, error) {
	if len(key) != 8 {
		return nil, KeySizeError(len(key))
	}

	c := new(desCipher)
	c.generateSubkeys(key)
	return c, nil
}

func (c *desCipher) BlockSize() int { return BlockSize }

func (c *desCipher) Encrypt(dst, src []byte) { encryptBlock(c.subkeys[:], dst, src) }

func (c *desCipher) Decrypt(dst, src []byte) { decryptBlock(c.subkeys[:], dst, src) }


```
注意，上面的 desCipher 实现了 BlockCipher 接口的三个方法，即`BlockSize() int`、`Encrypt(dst, src []byte)` 以及 `Decrypt(dst, src []byte)`

#### DES 的实现

##### <label id=imp_keyschedule>DES 实现之生成16轮中的subkeys</label>
subkey 的生成可以实现如下，结合上面的<a href="#sec_keyschedule">key schedule</a>的流程图看哦😁
```golang
// creates 16 56-bit subkeys from the original key
func (c *desCipher) generateSubkeys(keyBytes []byte) {
	// apply PC1 permutation to key
	key := binary.BigEndian.Uint64(keyBytes)
	permutedKey := permuteBlock(key, permutedChoice1[:])

	// rotate halves of permuted key according to the rotation schedule
	leftRotations := ksRotate(uint32(permutedKey >> 28))
	rightRotations := ksRotate(uint32(permutedKey<<4) >> 4)

	// generate subkeys
	for i := 0; i < 16; i++ {
		// combine halves to form 56-bit input to PC2
		pc2Input := uint64(leftRotations[i])<<28 | uint64(rightRotations[i])
		// apply PC2 permutation to 7 byte input
		c.subkeys[i] = permuteBlock(pc2Input, permutedChoice2[:])
	}
}

// PC-1 和 PC-2 的置换规则见下面的两个"表"
// Used in the key schedule to select 56 bits
// from a 64-bit input.
var permutedChoice1 = [56]byte{
	7, 15, 23, 31, 39, 47, 55, 63,
	6, 14, 22, 30, 38, 46, 54, 62,
	5, 13, 21, 29, 37, 45, 53, 61,
	4, 12, 20, 28, 1, 9, 17, 25,
	33, 41, 49, 57, 2, 10, 18, 26,
	34, 42, 50, 58, 3, 11, 19, 27,
	35, 43, 51, 59, 36, 44, 52, 60,
}

// Used in the key schedule to produce each subkey by selecting 48 bits from
// the 56-bit input
var permutedChoice2 = [48]byte{
	42, 39, 45, 32, 55, 51, 53, 28,
	41, 50, 35, 46, 33, 37, 44, 52,
	30, 48, 40, 49, 29, 36, 43, 54,
	15, 4, 25, 19, 9, 1, 26, 16,
	5, 11, 23, 8, 12, 7, 17, 0,
	22, 3, 10, 14, 6, 20, 27, 24,
}

// 16轮中生成subkey的循环左移规则如下
// Size of left rotation per round in each half of the key schedule
var ksRotations = [16]uint8{1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 1}

// creates 16 28-bit blocks rotated according
// to the rotation schedule
func ksRotate(in uint32) (out []uint32) {
	out = make([]uint32, 16)
	last := in
	for i := 0; i < 16; i++ {
		// 28-bit circular left shift
		left := (last << (4 + ksRotations[i])) >> 4
		right := (last << 4) >> (32 - ksRotations[i])
		out[i] = left | right
		last = out[i]
	}
	return
}


```


#### <lable id="imp_ip">DES 实现之 Initial Permutation</label>

```golang
// permuteInitialBlock is equivalent to the permutation defined
// by initialPermutation.
func permuteInitialBlock(block uint64) uint64 {
	// block = b7 b6 b5 b4 b3 b2 b1 b0 (8 bytes)
	b1 := block >> 48
	b2 := block << 48
	block ^= b1 ^ b2 ^ b1<<48 ^ b2>>48

	// block = b1 b0 b5 b4 b3 b2 b7 b6
	b1 = block >> 32 & 0xff00ff
	b2 = (block & 0xff00ff00)
	block ^= b1<<32 ^ b2 ^ b1<<8 ^ b2<<24 // exchange b0 b4 with b3 b7

	// block is now b1 b3 b5 b7 b0 b2 b4 b7, the permutation:
	//                  ...  8
	//                  ... 24
	//                  ... 40
	//                  ... 56
	//  7  6  5  4  3  2  1  0
	// 23 22 21 20 19 18 17 16
	//                  ... 32
	//                  ... 48

	// exchange 4,5,6,7 with 32,33,34,35 etc.
	b1 = block & 0x0f0f00000f0f0000
	b2 = block & 0x0000f0f00000f0f0
	block ^= b1 ^ b2 ^ b1>>12 ^ b2<<12

	// block is the permutation:
	//
	//   [+8]         [+40]
	//
	//  7  6  5  4
	// 23 22 21 20
	//  3  2  1  0
	// 19 18 17 16    [+32]

	// exchange 0,1,4,5 with 18,19,22,23
	b1 = block & 0x3300330033003300
	b2 = block & 0x00cc00cc00cc00cc
	block ^= b1 ^ b2 ^ b1>>6 ^ b2<<6

	// block is the permutation:
	// 15 14
	// 13 12
	// 11 10
	//  9  8
	//  7  6
	//  5  4
	//  3  2
	//  1  0 [+16] [+32] [+64]

	// exchange 0,2,4,6 with 9,11,13,15:
	b1 = block & 0xaaaaaaaa55555555
	block ^= b1 ^ b1>>33 ^ b1<<33

	// block is the permutation:
	// 6 14 22 30 38 46 54 62
	// 4 12 20 28 36 44 52 60
	// 2 10 18 26 34 42 50 58
	// 0  8 16 24 32 40 48 56
	// 7 15 23 31 39 47 55 63
	// 5 13 21 29 37 45 53 61
	// 3 11 19 27 35 43 51 59
	// 1  9 17 25 33 41 49 57
	return block
}
```



#### <label id="imp_fp">DES 实现之 Final Permutation</label>

```golang
// permuteInitialBlock is equivalent to the permutation defined
// by finalPermutation.
func permuteFinalBlock(block uint64) uint64 {
	// Perform the same bit exchanges as permuteInitialBlock
	// but in reverse order.
	b1 := block & 0xaaaaaaaa55555555
	block ^= b1 ^ b1>>33 ^ b1<<33

	b1 = block & 0x3300330033003300
	b2 := block & 0x00cc00cc00cc00cc
	block ^= b1 ^ b2 ^ b1>>6 ^ b2<<6

	b1 = block & 0x0f0f00000f0f0000
	b2 = block & 0x0000f0f00000f0f0
	block ^= b1 ^ b2 ^ b1>>12 ^ b2<<12

	b1 = block >> 32 & 0xff00ff
	b2 = (block & 0xff00ff00)
	block ^= b1<<32 ^ b2 ^ b1<<8 ^ b2<<24

	b1 = block >> 48
	b2 = block << 48
	block ^= b1 ^ b2 ^ b1<<48 ^ b2>>48
	return block
}

```

#### <label id="imp_feistelfunc">DES 实现之 Feistel Function</label>
还是要结合上面<a href="#sub_feistelfunc">Feistel Function</a> 的步骤来看哦😁
```golang
// DES Feistel function
func feistel(right uint32, key uint64) (result uint32) {
	sBoxLocations := key ^ expandBlock(right)
	var sBoxResult uint32
	for i := uint8(0); i < 8; i++ {
		sBoxLocation := uint8(sBoxLocations>>42) & 0x3f
		sBoxLocations <<= 6
		// row determined by 1st and 6th bit
		// column is middle four bits
		row := (sBoxLocation & 0x1) | ((sBoxLocation & 0x20) >> 4)
		column := (sBoxLocation >> 1) & 0xf
		sBoxResult ^= feistelBox[i][16*row+column]
	}
	return sBoxResult
}

// 第一步中的Expansion
// expandBlock expands an input block of 32 bits,
// producing an output block of 48 bits.
func expandBlock(src uint32) (block uint64) {
	// rotate the 5 highest bits to the right.
	src = (src << 5) | (src >> 27)
	for i := 0; i < 8; i++ {
		block <<= 6
		// take the 6 bits on the right
		block |= uint64(src) & (1<<6 - 1)
		// advance by 4 bits.
		src = (src << 4) | (src >> 28)
	}
	return
}

```

#### <label id="imp_enc">DES 实现之加密、解密</label>

```golang
// Encrypt one block from src into dst, using the subkeys.
func encryptBlock(subkeys []uint64, dst, src []byte) {
	cryptBlock(subkeys, dst, src, false)
}

// Decrypt one block from src into dst, using the subkeys.
func decryptBlock(subkeys []uint64, dst, src []byte) {
	cryptBlock(subkeys, dst, src, true)
}

// 加密与解密的不同点只在于subkeys的次序的不同😏
func cryptBlock(subkeys []uint64, dst, src []byte, decrypt bool) {
	b := binary.BigEndian.Uint64(src)
	b = permuteInitialBlock(b)
	left, right := uint32(b>>32), uint32(b)

	var subkey uint64
	for i := 0; i < 16; i++ {
		if decrypt {
			subkey = subkeys[15-i]
		} else {
			subkey = subkeys[i]
		}

		left, right = right, left^feistel(right, subkey)
	}
	// switch left & right and perform final permutation
	preOutput := (uint64(right) << 32) | uint64(left)
	binary.BigEndian.PutUint64(dst, permuteFinalBlock(preOutput))
}

```

### 证明 DES 的解密过程与加密过程只需要将subkeys 颠倒即可
具体见文档[des_proof](./des_proof.pdf)


## 汇总
1. DES 中的替换表和置换规则（比如 IP、FP、Expansion function、Permutation 等): https://en.wikipedia.org/wiki/DES_supplementary_material

