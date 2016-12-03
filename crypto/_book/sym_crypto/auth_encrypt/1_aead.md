# Crypto 学习札记之 Authenticated Encryption 

## 1. [Authenticated encryption](https://en.wikipedia.org/wiki/Authenticated_encryption) 定义
Authenticated Encryption (AE) 亦称为 Authenticated Encryption with Associated Data (AEAD) ，此种模式既实现了对数据
加密，又通过将消息结合额外的 associated data 计算得到的 MAC 提供了对消息的认证及数据完整性的保护；

AEAD 模式其实只是定义了统一的编程接口，任何实现了该机制的cipher均需要实现如下的方法，其中，
- 加密： 对应`Seal`方法
  - 输入：plaintext, key, optionally a header in plaintext (即associated data, 注意该header不会被加密的, 但是会被提供认证保护)
  - 输出：ciphertext, authentication tag (即 Message Authentication Code).
- 解密：对应`Open`方法
  - 输入：ciphertext, authentication tag (MAC), optionally a header.
  - 输出：plaintext, an error if the authentication tag does not match the supplied ciphertext or header.

The header part is intended to provide authenticity and integrity protection for networking or storage metadata for which 
confidentiality is unnecessary, but authenticity is desired. 比如TLS Record 协议中的 record header.

In addition to protecting message integrity and confidentiality, authenticated encryption can provide plaintext awareness and
security againts [chosen ciphertext attack](https://en.wikipedia.org/wiki/Chosen-ciphertext_attack).  In these attacks, an 
adversary attempts to gain an advantage against a cryptosystem (比如，关于secret decryption key的信息) by submitting carefuly 
chosen ciphertexts to some ["decryption oracle"](https://en.wikipedia.org/wiki/Padding_oracle_attack) and analyzing the decrypted results.
而authenticated encryption scheme 可以识别出那些伪造的ciphertexts，并且拒绝解密它们😏.  This in turn prevents the attacker from requesting 
the decryption of any ciphertext unless he generated it correctly using the encryption algorithm, which would imply that he already knows
the plaintext. 


### 1.1 Approaches to Authenticated Encryption
ISO/IEC 19772:2009 标准中列了六种不同的authenticated encryption modes:
1. OCB 2.0
2. Key Wrap
3. CCM
4. EAX
5. Enrypt-then-MAC (EtM)
6. Galois/Counter Mode (GCM)

另外，[sponge functions](https://en.wikipedia.org/wiki/Sponge_function) can be used in duplex mode to provide authenticated encryption.

Many specialized authenticated encryption modes have been developed for use with symmetric block ciphers. 
但是，其实只要将某种encryption scheme 和 一个MAC结合，便可以组成一种authenticated encryption, 只要满足
下面两个条件：
- The encryption scheme is semantically secure under a chosen plaintext attack.
- The MAC function is unforgeable under a chosen message attack.

### 1.2 AE 算法之encryption scheme + MAC 的三种组合顺序
下面来说说encryption scheme + MAC 组合形成的AE modes:
#### 1.2.1 Encrypt-then-MAC (EtM)
此种方法的安全指数最高，用在IPsec中，而TLS 和 DTLS 扩展中的 ciphersuites 也提供了 EtM. 
具体的流程如下图所示，首先是加密明文得到密文 ciphertext，然后计算<b>密文 ciphertext</b> 的 MAC, 
注意，加密以及计算 MAC 的 Key 是相同的。

![Encrypt-then-MAC (EtM)](https://upload.wikimedia.org/wikipedia/commons/b/b9/Authenticated_Encryption_EtM.png)


#### 1.2.2 Encrypt-and-MAC (E&M)
SSH 中用的就是 E&M, 该方法使用 Key 加密明文得到密文 ciphertext, 同时使用相同的 Key、对<b>明文</b>应用MAC 算法，取得MAC。

![Encrypt-and-MAC (E&M)](https://upload.wikimedia.org/wikipedia/commons/a/a5/Authenticated_Encryption_EaM.png)


#### 1.2.3 MAC-then-Encrypt (MtE)
SSL/TLS 中用到了 MtE 方法，首先使用 Key、对明文 plaintext 应用MAC 算法，得到对应的 MAC，然后再用相同的 Key 对 plaintext_MAC 进行加密，
得到ciphertext. 注意，与EtM、E&M 相比，最大的不同点在于前者都会把 MAC 拼接到 ciphertext 后面，即 ciphertext_MAC, ciphertext 是不包含MAC的，
但是这种方法也对MAC进行加密了，最后生成的只有ciphertext. MtE 的流程图如下所示：

![MAC-then-Encrypt (MtE)](https://upload.wikimedia.org/wikipedia/commons/a/ac/Authenticated_Encryption_MtE.png)



