# Intro
These notes are just a glimpse of what I have learned in these days. 
Recently, I tried to read the source codes of IBM hyperledger project to have a better understanding of blockchain.
I found it a need to prepaer myself with some knowledge in specific field, like cryptographics. 
And it turned out that writting is really a good way.  It's not just about recording those ephemeral thoughts, but as I 
try to find a way to express logically, those unintelligible ideas seems to become less obscure.

## [Cryptographic](./crypto)
  * [1. Symmetry Cryptography ](sym_crypto/README.md)
    * [1.1 Data Encryption Standard](sym_crypto/des/des.md)
    * [1.2 Advanced Encryption Standard](sym_crypto/aes/README.md)
      * [1.2.1 Basic Number Theory -- Euclidean Algorithm ](sym_crypto/aes/euclid.md)
      * [1.2.2 Basic Number Theory -- Galois Field ](sym_crypto/aes/galois.md)
      * [1.2.3 Advanced Encryption Algorithm](sym_crypto/aes/aes.md)
    * [1.3 Operation Mode of Block Cipher](sym_crypto/operation_mode/README.md)
      * [1.3.1 Operation Mode of Block Cipher](sym_crypto/operation_mode/1_blockciphermode.md)
      * [1.3.2 Cipher Block Chaining Mode](sym_crypto/operation_mode/2_cbc.md)
      * [1.3.3 Cipher FeedBack Mode](sym_crypto/operation_mode/3_cfb.md)
      * [1.3.4 Output FeedBack Mode](sym_crypto/operation_mode/4_ofb.md)
      * [1.3.5 Counter Mode](sym_crypto/operation_mode/5_ctr.md)

## [gRPC](./grpc)
These notes focus on google Remote Procedure Call and protocol buffer.
  * [1. Google Protocol Buffer](grpc/proto.md)
  * [2. Google Remote Procedure Call](grpc/grpc.md)
    * [2.1 The Types of gRPC Methods](grpc/method/README.md)
      * [2.1.1 The Simplest RPC Method](grpc/method/simple.md)
      * [2.1.2 The Server-side Streaming RPC Method](grpc/method/serverstream.md)
      * [2.1.3 The Client-side Streaming RPC Method](grpc/method/clientstream.md)
      * [2.1.4 The Bidirectional Streaming RPC Method](grpc/method/bistream.md)
    * [2.2 gRPC Authenticaton](grpc_auth.md)
