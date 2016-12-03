# Block cipher 学习札记之 AES

## Advanced Encryption Standard

### 综述

For the AES algorithm, the length of the input block, the output block and the State is 128 bits. This is represented by Nb = 4, 
which reflects the number of 32-bit words (number of columns) in the State.

For the AES algorithm, the length of the Cipher Key, K, is 128, 192, or 256 bits. The key length is represented by Nk = 4, 6 or 8, 
which reflects the number of 32-bit words (number of columns) in the Cipher Key.

For the AES algorithm, the number of rounds to be performed during the execution of the algorithm is ependent on the key size. 
The number of rounds is represented by Nr, where 
- Nr=10 when Nk=4, and Nb=4
- Nr=12 when Nk=6, and Nb=4
- Nr=14 when Nk=8, and Nb=4

For both its Cipher and Inverse Cipher, the AES algorithm uses a round function that is composed of four different byte-oriented transformations:
1. byte substitution using a substitution table (S-box),
2. shifting rows of the State array by different offsets
3. mixing the data within each column of the State array
4. adding a Round Key to the State，其实就是异或操作

### 加密 Cipher 

伪代码可以描述如下：
```C
Cipher

```

## 2. Rijndael Key Schedule
[Rijndael key schedule](https://en.wikipedia.org/wiki/Rijndael_key_schedule) 是AES (Rijndael) 用来将一个 short key 扩展成为 
a number of separate round keys. AES 的三个版本（秘钥长度分别为128、192、256位，rounds的数目分别为10、12、14）在每一轮的转换
中的最后一步均需要异或上一个独立的128位的 round key. 而这个key schedule 从最初的key生成了每一轮需要的keys.

### 2.1 Common operations 
Rijndael's key schedule 中使用了如下几种操作：
1. Rotate: 循环左移
2. Rcon: 其实就是有限域上的乘法运算

   >  <img src="http://chart.googleapis.com/chart?cht=tx&chl= \mathit{Rcon(i)} =  n^{i-1} 
= \underbrace{n \cdot n \cdot n \ldots}_{i-1}  \mathit{ , where n means polynomial n(x) = x" style="border:none;">
   >
    其中，<img src="http://chart.googleapis.com/chart?cht=tx&chl= n \cdot n " style="border:none;"> 表示Rijndael Finite Field GF(2^8) 上的乘法运算，
   该有限域使用不可约减多项式是<img src="http://chart.googleapis.com/chart?cht=tx&chl= \mathit{ p(x) = x^8 %2B x^4 %2B x^3 %2B x^1 %2B 1} " style="border:none;"> 
   ，此乘法运算可以表示如下：
    >  <img src="http://chart.googleapis.com/chart?cht=tx&chl= \mathit{ n \cdot n = n(x) \ast n(x) = n << 1, if the n*n < 2^8} " style="border:none;"> 
    > 
    >  <img src="http://chart.googleapis.com/chart?cht=tx&chl= \mathit{ n \cdot n = n(x) \ast n(x) modulo p(x) = (n <\!< 1) \oplus 0x1b, if n*n \geq 2^8 } " style="border:none;"> 

3. Sbox: The [Rijndael S-box](https://en.wikipedia.org/wiki/Rijndael_S-box) is a matrix used in the Rijndael cipher, which the AES 
    cryptographic algorithm was based on. The S-box (substitution box) servers as a lookup table. 总共有两种：
    - Forward S-box
    - Inverse S-box

4. Key schedule core



## 汇总
1. Advanced Encryption Standard: http://csrc.nist.gov/publications/fips/fips197/fips-197.pdf
2. Rijndael Key Schedule: https://en.wikipedia.org/wiki/Rijndael_key_schedule
3. Rijndael S-box: https://en.wikipedia.org/wiki/Rijndael_S-box

