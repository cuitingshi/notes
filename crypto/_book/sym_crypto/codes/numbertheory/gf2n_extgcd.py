
# compute a % b, where a, b are in Galois Field GF(2^n)
# return remainder
# suppose a > b, 最高位在左边
def gf2nMod(a, b):
    if (a < b):
        return a
    elif (a == b):
        return 0
    i = 0
    div = b
    while ( a >= div):
        div <<= 1
        i += 1
    a ^= (b << (i-1))
    return gf2nMod(a, b)


def gf2nMul(a, b, n, r):
    accumulator = 0
    while (b!=0):
     #   print "before shifting, a = 0x%x, b = 0x%x, accumulator = 0x%x" % (a, b, accumulator)
        if (b&1):
            accumulator ^= a
        b >>= 1
        if ( a & 1<<n):
            a = ((a & ~(1<<n))<<1)  ^r
        else:
            a <<= 1
     #   print "after shifting, a = 0x%x, b = 0x%x, accumulator = 0x%x" % (a,b,accumulator)
    return accumulator



# compute gcd(a, b) = ax + by
# return gcd(a, b), x, y
def gf2nExtGcd(a, b):
    if (b==0):
        return a, 1, 0
    r, x2, y2 = gf2nExtGcd(b, a%b)
    x = y2
    y = x2 ^ gf2nMul(a/b, y2, 8,)
    return r, x, y

if __name__ == '__main__':

