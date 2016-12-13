> 2016年 12月 13日 星期二 00:35:19 CST

# 公钥密码体系之 RSA 算法

## Operation of RSA
RSA 算法只要有四个步骤：
1. key generation
2. key distribution
3. encryption
4. decryption

### Key Generation
RSA involves a public key and a private key. The basic principle behind RSA is the observation that it is practical to find three very large positive integers e, d and n 使得如下式子成立:
$$ (m^e)^d \equiv m (mod\ n)$$
注意，即使知道 e 和 n 甚至 m 也难以找到 d

此外，对于一些操作，it is convenient that the order of the two exponentiations can be changed and that this relation also implies:
$$ (m^d)^e \equiv m (mod\ n)$$

### Key Distribution
To enable Bob to send his encrypted messages, Alice transmits her public key (n, e) to Bob via a reliable, but not necessarily secret route. The private key d is never distributed.

### Encryption
假设 Bob 要发送消息 M 给 Alice.

首先 Bob 要把消息 M 转换为整数 m, 使得 0 <= m < n 而且 gcd(m, n) = 1. 注意，可能消息需要补上一些数字-- padding scheme. 然后他利用 Alice 的公钥 e 计算出密文 c, 可以表示如下:
$$ c \equiv m^e (mod\ n)$$

所以，其实 RSA是一个分组加密算法 :Smile: 

### Decryption
Alice 可以使用私钥 d 从密文 c 中恢复出明文 m, 公式表示如下：
$$ c^d \equiv (m^e)^d \equiv m (mod\ n)$$

## 算法实现描述
### Key Generation 算法


## 汇总
1. RSA Wiki: https://en.wikipedia.org/wiki/RSA_(cryptosystem)







