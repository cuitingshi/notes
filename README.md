---
search: false
---

# Introduction
Recently, I tried to read the source codes of IBM hyperledger project to have a better understanding of blockchain.
I found it a need to prepare myself with some knowledge in specific fields, like cryptography. 
And it turned out that writing was an effective way.  It's not just about keeping track of what I have learned. 
Instead, as I tried to find a way to express myself more logically, those unintelligible ideas seemed to become less obscure. 
Those ephemeral thoughts just came out like a spring.😁 Really amazing, I should keep following it~ 
  By the way, the notes are also available as [gitbook html pages](https://xyzlol.gitbooks.io/notes/content/).

## [Cryptographic](./crypto)
  * [1. Symmetry Cryptography ](crypto/sym_crypto/README.md)
    * [1.1 Data Encryption Standard](crypto/sym_crypto/des/des.md)
    * [1.2 Advanced Encryption Standard](crypto/sym_crypto/aes/README.md)
      * [1.2.1 Basic Number Theory -- Euclidean Algorithm ](crypto/sym_crypto/aes/euclid.md)
      * [1.2.2 Basic Number Theory -- Galois Field ](crypto/sym_crypto/aes/galois.md)
      * [1.2.3 Advanced Encryption Algorithm](crypto/sym_crypto/aes/aes.md)
    * [1.3 Operation Mode of Block Cipher](crypto/sym_crypto/operation_mode/README.md)
      * [1.3.1 Operation Mode of Block Cipher](crypto/sym_crypto/operation_mode/1_blockciphermode.md)
      * [1.3.2 Cipher Block Chaining Mode](crypto/sym_crypto/operation_mode/2_cbc.md)
      * [1.3.3 Cipher FeedBack Mode](crypto/sym_crypto/operation_mode/3_cfb.md)
      * [1.3.4 Output FeedBack Mode](crypto/sym_crypto/operation_mode/4_ofb.md)
      * [1.3.5 Counter Mode](crypto/sym_crypto/operation_mode/5_ctr.md)
    * [1.4 Random Number Generator](crypto/sym_crypto/randnum/README.md)
      * [1.4.1 Pseudo-random Number Generator](crypto/sym_crypto/randnum/prng.md)
      * [1.4.2 Revest Cipher 4 Algorithm](crypto/sym_crypto/randnum/rc4.md)

## [gRPC](./grpc)
 These notes focus on Google Remote Procedure Call and protocol buffer.
  * [1. Google Protocol Buffer](grpc/proto.md)
  * [2. Google Remote Procedure Call](grpc/grpc.md)
    * [2.1 The Types of gRPC Methods](grpc/method/README.md)
      * [2.1.1 The Simplest RPC Method](grpc/method/simple.md)
      * [2.1.2 The Server-side Streaming RPC Method](grpc/method/serverstream.md)
      * [2.1.3 The Client-side Streaming RPC Method](grpc/method/clientstream.md)
      * [2.1.4 The Bidirectional Streaming RPC Method](grpc/method/bistream.md)
    * [2.2 gRPC Authenticaton](grpc/grpc_auth.md)

## [Nginx](./nginx)
  * [Elementary Tutorial](nginx/beginner_guide.md)
  * [Used as a Load Balancer](nginx/http_load_balancer.md)
