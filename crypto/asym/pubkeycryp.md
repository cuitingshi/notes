> 2016年 12月 12日 星期一 23:11:21 CST

# Public Key Cryptography
Public Key Cryptography, or asymmetric cryptography, 即公钥密码体制, is any cryptographic 
system that uses pairs of keys: public keys which may be disseminated widely, and 
private keys which are known only to the owner.

主要实现两个功能：
- authentication, 其中 public key is used to verify that a holder of the paired private key 
set the message
- encryption, 其中 the holder of the paired private key can decrypt the message encrypted with the public key.

Public key cryptography systems often rely on cryptographic algorithms based on mathematical 
problems that currently admit no efficient solution -- particularly those inherent in 
- certain integer factorization
- discrete algorithm
- elliptic curve relationships

但是，由于非对称加密的计算复杂性，它经常只适合用于 small blocks of data, 通常是 the transfer of a symmetric encryption key (e.g. a session key). This symmetric key 之后会被用来加密剩下的那些可能非常长的消息序列。毕竟，the symmetric encryption/decryption is based on simpler algorithms and is much faster.

公钥密码体制的应用：

| 算法 | 加密/解密 | 数字签名 | 密钥交换 |
| ---  | --------  | -------  | -------  |
| RSA  | 是		   | 是		  | 是		 |
| 椭圆曲线 | 是    | 是		  | 是 		 |
| Diffie-Hellman | 否 | 否 	  | 是		 |
| DSS  | 否 	   | 是		  | 否		 |


A central problem with the use of public key cryptography is confidence/proof that a particular public key is authentic, in that it is correct and belongs to the person or entity claimed, and has not been tampered with or replaced by a malicious third party. 解决这个问题的一个方法是使用 a public key infrastructure (PKI), in which one or more third parties - known as certificate authorities - certify ownership of the key pairs. PGP, in addition to being a certificate authority structure, has used a scheme generally called the "web of trust", which decentralizes such authentication of public keys by a central mechanism, and substitutes individual endorsements of the link between user and public key. 


