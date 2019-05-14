# Galois Field Multiplication 实现算法
有限域 $GF(2^{n}) $
上的乘法运算可以利用 [Peasant or binary multiplication algorithm][1]
来实现，下面先来说一下Peasant's algorithm

## Peasant's Algorithm
不得不说，这个算法简直是二进制系统的鼻祖吖😂，其实它就是简单粗暴地每次只乘以2（对应移位操作），如果有余数则需要执行加法操作.
具体的数学运算见[Russian Peasant Multiplication][2]。

下面来说一下作为算法的[Russian Peasant's Algorithm][3],

基本的思想是如果要计算n\*m, 则可以转换为如下的运算：
- 如果n是偶数， 则可以转换为计算 $\frac{n}{2} \ast 2m $
- 如果n是奇数，则可以转换为计算 $\frac{n-1}{2} \ast 2m + m $

因此计算的复杂性为
$$
T(n) \leq T(\frac{n}{2}) + \Theta{(1)} = \Theta{(\lg{(n)})}
$$

对应的代码如下所示
```go
func RussianPeasantMultiply(n, m int) int{
    var accumulator int = 0
    while m != 0 {
      if m & 1 == 1 {
          accumulator += n
      }
      m = m >> 1
      n = n << 1
    }
    return accumulator
}

```

如果仅仅将上述思想仅仅用于简单的算术运算的话，那么就有点浪费人才了😂，
其实在polynomial arithmetic, modular arithmetic, 有限域 $GF(2^{n}) $
上的乘法运算它都可以大展身手的，
[戳这里][4]

1. 用来计算 interger exponentiation : \\
  - 如果 m 是偶数，则有 $n^{m} = (n \times n)^{\frac{m}{2}} $
  - 如果 m 是奇数，则有 $n^{m} = (n \times n)^{\frac{m-1}{2}} \times n $
```go
func RPexp(n, m int) int {
  var accumulator int = 1
  while m != 0 {
    if m & 1 == 1 {
      accumulator *= n
    }
    m = m >> 1
    n *= n
  }
  return accumulator
}
```
2. 用来计算 multiplication in GF(2): 这里类似于上面的用来计算普通乘法的函数`RussianPeasantMultiply(n, m int) int`, 
  只不过因为GF(2)上的加法运算是异或运算（加法的结果只能是0或者1😁）
  ```go
  func RussianPeasantMultiplyGF2(n, m int) int {
    var acumulator int = 0;
    while m != 0 {
      if m & 1 == 1 {
        accumulator ^= n
      }
      m = m >> 1
      n = n << 1
    }
    return accumulator
  ```


## Galois Field GF(2^N) 上的运算
### 乘法运算
有限域GF(2^N) 上的乘法运算是多项式取模运算, 即乘法的结果如果大于2^N，则需要将该结果 modulo 不可约减多项式p(x), 可以表示如下：

$$
\forall n, m \in GF(2^{N}), \ 

n \cdot m = ( \sum_{i=0}^N{n_i x^i} ) \ast ( \sum_{i=0}^N{m_i  x^i} ) \mathit{\  mod \ } p(x) , \  if \  n \ast m \ge 2^N 
$$

$$ n \cdot m = ( \sum_{i=0}^N{n_i x^i} ) \ast ( \sum_{i=0}^N{m_i  x^i}), if \ n \ast m \ge 2^N $$


### 加减法运算 
有限域GF(2^N) 上的加法运算和减法运算都是系数运算，其中每个系数进行普通的加减、然后模以2的运算, 即 $$(m_{i} + n_{i}) \% 2 $$

因此，有限域GF(2^N) 的加法、减法运算是等同于异或运算的,下面用公式来表示一下该有限域上的加法运算和减法运算。

$$
\forall n, m \in GF(2^{N}), \ 
n \dot + m = \sum_{i=0}^N{(n_i + m_i) \  \% 2 } \ast x^{i} = \sum_{i=0}^N{n_i \oplus m_i \ast x^i} 
$$

$$ n \dot - m = \sum_{i=0}^N{(n_i -  m_i) \% 2 \ast x^i} = \sum_{i=0}^N{n_i \oplus m_i \ast x^i}$$

故有，
$$ n \dot + m =  n \dot - m $$


## Rijndael Finite Field Multiplication 实现算法
Rijndael 有限域其实是乘法运算中使用不可约减多项式<img src="http://chart.googleapis.com/chart?cht=tx&chl= p(x) = x^8 %2B x^4 %2B x^3 %2B x^1 %2B 1" style="border:none;"> 的
Galois Field <img src="http://chart.googleapis.com/chart?cht=tx&chl= GF(2^8)" style="border:none;"> 
该有限域上的乘法运算可以表示如下：

$$ 
\forall n, m \in GF(2^8), \   
n \cdot m = ( \sum_{i=0}^7{n_i x^i} ) \ast ( \sum_{i=0}^7{m_i  x^i}) \mathit {\  mod \ } p(x), \ if\  n \ast m \ge 2^8
$$

$$ n \cdot m = ( \sum_{i=0}^7{n_i x^i} ) \ast ( \sum_{i=0}^7{m_i  x^i}),\ if\  n \ast m < 2^8 $$

则这个乘法运算可以使用 a modified version of the "peasant's algorithm" 来实现, 
结合Peasant's Multiplication 乘法的思想，对于上面这个式子，可以表示成
 -  如果 m 是偶数，则有
$$
n \cdot m = [ ( \sum_{i=0}^{7}{n_i x^i} )  \cdot x ] \mathit{  } \cdot  [ ( \sum_{i=0}^{7}{m_i x^{i}} ) \div x  ] \Rightarrow
n  \cdot m  = (n \cdot x) \cdot (m \div x)
$$

 - 如果 m 是奇数，则有
$$
n \cdot m = \sum_{i=0}^7{n_i x^i}\   \dot +  \ [ (\sum_{i=0}^7{n_i x^i}) \cdot x ] \  \cdot \  [ ( \sum_{i=0}^7{m_i  x^i} ) \div x ] \Rightarrow
n \cdot m = n \dot + (n \cdot x) \cdot ( (m \dot - 1) \div x)
$$

因此，可以实现如下, 算法的文字版见[此材料中的Multiplication 下的Rijndael's finite field 的描述][5]：
```go
// 有限域GF(2^n)上的乘法，其中不可约减多项式是 p(x) = x^n + r(x)
// 计算 n * m mod p
// 注意，下面都是高阶系数在左
func RPMultGF2n(n, m, r int8) int {
  var accumulator int8 = 0
  while m != 0 {
    if m & 1 == 1 {
      accumulator ^= n
    }
    m >>= 1
    // 计算 n \cdot x
    if (n >> 7 & 1) == 1 { // leftmost bit is 1
      n = n << 1 ^ r // 对应上面的 n * x modulo p
    }else{
      n <<= 1
    }
  }
  return accumulator
}

func RPMultRijndaelField(n, m) {
  var r int8 = 0x15
  return RPMultGF2n(n, m, r)
}

```

有没有用简单的Russian Peasant's Multiplication 的思想来实现有限域GF(2^N) 上的乘法，
再结合移位操作来实现很巧妙啊😉，其实GCM的实现中也用到的哦

[1]: https://en.wikipedia.org/wiki/Multiplication_algorithm#Peasant_or_binary_multiplication "Russian Peasant Multiplication"
[2]: http://www.cut-the-knot.org/Curriculum/Algebra/PeasantMultiplication.shtml "Peasant Multiplication"
[3]: http://www.cs.yale.edu/homes/aspnes/pinewiki/RussianPeasantsAlgorithm.html "Russian Peasant Algorithm"
[4]: https://www.embeddedrelated.com/showarticle/760.php "Russian Peasant Algorithm 应用"
[5]: https://en.wikipedia.org/wiki/Finite_field_arithmetic#Rijndael.27s_finite_field "Rijndael Finite Field"
