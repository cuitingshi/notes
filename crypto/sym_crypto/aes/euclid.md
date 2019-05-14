## The Euclidean Algorithm 欧几里得算法
[欧几里得算法][1] 是用来计算两个数的最大公约数的

欧几里德定理可以表示如下：
$$ 
gcd(a, b) = gcd(b, a \% b)
$$

用于计算两个正整数 a 和 b 的最大公因子的Standard Euclidean algorithm 可以描述如下：

1. Set the value of the variable c to the larger of the two values a and b, and set d to the smaller of a and b.
2. Find the remaindr when c is divided by d. Call this remainder r.
3. If r = 0, then gcd(a, b) = d. Stop.
4. Otherwise, use the current values of d and r as the new values of c and d, respectivelly, and go back to step 2.


该算法的实现可以如下：
```go
// 欧几里得算法计算a, b的最大公约数
func gcd_euclid(a, b int) int {
  if a%b == 0 {
    return b
  }
  return gcd_euclid(b, a%b)
}
```

## The Extended Euclidean Algorith m扩展的欧几里得算法 
用处：有限域及RSA等密码算法

The Euclidean algorithm, which is used to find the greates common divisor of two integers, 
can be extended to solve linear Diophantine equations.

### The division algorithm

**Thearem 1. Division algorithm** Given any two positive intergers n and d, there exist intergers q and r (respectively called the quotient 
and the remainder) such that

$$
 n = q \ast d + 4 and 0 \leq r < d
$$

### Our goal 
The standard Euclidean algorith gives the greatest common divisor and nothing else. However, 
if we keep track of a bit more information as we go through the algorithm, we can discover how 
to write the greatest common divisor as an interger linear combination of the two original numbers. 
In other words, we can find intergers s and t such that

$$
 gcd(a, b) = s \ast a + t \ast b
$$


注意到，由于 gcd(a, b) 通常要小于a、b， 因此 s 或者 t 中的一个通常是负数😁


The extended Euclidean algorithm uses the same framework as the standard Euclidean algorithm, 
but there is a bit more bookkeeping. 

### The extended Euclidean algorithm
The extended Euclidean algorithm is used for finding the greatest common divisor of two positive integers and b and 
writing this greatest common divisor as an integer linear combination of a and b. 

算法描述如下：
1. Set the value of the variable c to the larger of the two values a and b, and set d to the smaller of a and b
2. Find the quotient and the remainder when c is divided by d. Call the quotient q and the remainder r. 
    Use the division algorithm and experessions for previous remainders to <font color="darkgreen">write an expressioon for r interms of a and b.</font>
3. If r = 0, then gcd(a, b) = d. <font color="darkgreen">The expression for the previous value of r gives an expression for gcd(a, b) interms of a and b.</font> Stop.
4. Otherwise, use the current values of d and r as the new values of c and d respectively, and go back to stop 2.

基本算法： 对于不完全为0的非负整数a、b, gcd(a, b) 表示a, b 的最大公约数， 必然存在整数x、y，使得 $gcd(a,b) = ax+ by $

**证明如下：**

设 a > b
1. 推理1： 显然当 b= 0时， gcd(a, b) = a. 此时 x =1, y = 0;
2. 推理2： 当ab!= 0 时，设 

$$
  a\ast x_1 + b \ast y_1 = gcd(a, b) ; 
  b\ast x_2 + (a \% b) \ast y_2 = gcd(b, a \% b) 
$$

根据 standard Euclidean Algorith gcd(a,b) = gcd(b, a%b) 有

$$a \ast x_1 + b \ast y_1 = b \ast x_2 + (a \% b) \ast y_2 $$
  
that is, 

$$a \ast x_1 + b \ast y_1 = b \ast x_2 + ( a - \frac{a}{b} \ast b ) \ast y_2 $$

故根据恒等定理可知： 
$$
x_1 = y_2; y_1 = x_2 - \frac{a}{b} \ast y_2 
$$

这样子，便可以得到了求解 $x_{1}, y_{1} $ 的方法： $x_{1}, y_{1} $ 的值可以基于 $x_{2},  y_{2} $ 来表示。 上面的思想便可以以递归的形式定义实现，
算法可实现如下：
```go
func extgcd(a, b int) ( r, x, y int) {
  if b == 0 {
    return a, 1, 0
  }
  var x2, y2 int
  r, x2, y2 = extgcd(b, a%b)
  x = y2
  y = x2 - (a/b) * y2
  return 
}
```

### 扩展欧几里得算法的应用
A common use of the extended Euclidean algorithm is to solve a linear Diophantine equation in two variables. Such an equation is of the form

$$
ax + by = c
$$
其中， a、b、c 是常量， x 和 y 是变量

有三种可能性：
#### Case 1: c = gcd(a, b)
这种情况最简单了，其实就是直接使用扩展的欧几里得算法就可以得到了。

#### Case 2: c is a multiple of gcd(a, b)
假设 c 是 gcd(a, b) 的倍数，即

$$ c = k \ast gcd(a, b), k \in N
$$

Then we can find a solution to the Diophantine equation `ax + by = c` by writing gcd(a, b) in terms of a and b 
and then multiplying the coefficients by k.

比如， consider the Diophantine equation: 
$$ 
1398x + 324y = 60 
$$

又因为 gcd(1389, 324) = 6, 根据 the extended Euclidean algorithm 我们可以知道：
$$ 
6 = -19 \ast 1398 + 82 \ast 324
$$

又因为 60 是 6 的倍数， 所以 we can use this to write 60 interms of 1398 and 324:
> 60 = 10 * (6)
>
>   = 10 * [ -19 * (1398) + 82 * (324) ]
>
>   = -190 * (1398) + 820 * (324)

因此， x = -190, y = 820 是这个 Diophantine equation 的一个解(其实还有很多其他解的，见下面的注解）

##### Aside: Generating more solutions
在上面两种情况中，我们都是使用 the extended Euclidean algorithm 来找到每个 Diophantine equation 的 <font color="red">一个解</font>而已。
其实，这些方程等式有<font color="red">无穷多的解</font>。

The extended Euclidean algorithm, if carried out all the way to the end, gives a way to write 0 in terms of the original numbers a and b.
We can add or subtract 0 as many times as we like without changing the value of an expression, and this is the basis for generating other 
solutions to a Diophantine equation, as long as we are given one initial solution.

比如说， 当 a= 1398，b = 324 时， we saw that the extended Euclidean algorithm produces the expression $0 = 54 \ast a - 233 \ast b $

so, $0 = 54 \ast (1398) - 233 \ast (324) $

Therefore, for the Diophantine equation  $1398x + 324y = 60 $

Suppose we know one value of x and one value of y that together form a solution to this equation. Since  $0 = 54\ast(1298) - 233\ast(324) $, 
if we add 54 to x and subtract 233 from y, we will produce another solution, 因为

> 1398(x+54) + 324(y-233) = 1398x + 1398*(54) + 324y + 324 *(-233)
>
>   = 1398x + 324y + [ 1398*(54) + 324 * (-233)]
>
> = 60

#### Case 3: c is not a multiple of gcd(a, b)
其实，如果 c 不是 gcd(a,b) 的倍数的话，那么一定不会存在整数 x、y 满足方程 `ax + by = c`. 
So the extended Euclidean algorithm is all we need -- it will give us all integer solutions if any exist, and otherwise there are no 
integer solutions to the Diophantine equation at all.


## Stein 算法
其实计算两个数的最大公约数的还有Stein 算法，该算法只有整数的移位和加减法，相比于Euclidean Algorithm, 该算法对于大素数更有优势.
算法可以描述如下:
```go
func gcdStein( a, b int) int {
  if a == 0 {
    return b
  }
  if b == 0 {
    return a
  }
  if a&1==0 && b&1==0 {
    return 2 * gcdStein(a>>1, b>>1)
  }else if a&1==0 {
    return gcdStein(a>>1, b)
  }else if b&1==0 {
    return gcdStein(a, b>>1)
  }else {
    return gcd( math.Abs((a-b), math.Min(a, b)) )
  }
}
```

## 应用情形总结
欧几里得算法可以用来求
- 两个普通整数的最大公因子
- 两个多项式的最大公因子 $gcd( a(x), b(x) ) $

扩展欧几里得算法可以用来求
- gcd(a, b) 以及满足 ax + by = gcd(a,b) 的x, y
- 普通的模运算中的乘法逆元 $ b^{-1} \ast b = 1 (mod\  n) $
  , 其实就是 $nx + by = 1 (mod\  n) \Rightarrow extgcd(n, b) $
  中返回的最大公因数必须为1，此外 y 就是 b 的乘法逆元
- 多项式乘法中 b(x) 以 a(x) 为模的乘法逆元, 只不过算法实现的时候，中间的加减法以及乘法运算都要依照多项式上的运算定义来进行




## 汇总
1. Euclidean Algorithm: https://en.wikipedia.org/wiki/Euclidean_algorithm
2. Euclidean Algorithm，Stein Algorithm, Extended Euclidean Algorithm: https://xuanwo.org/2015/03/11/number-theory-gcd/

[1]: https://en.wikipedia.org/wiki/Euclidean_algorithm "Euclidean Algorithm"
