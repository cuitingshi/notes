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

if __name__ == '__main__':
    a = 0x02
    b = 0x87
    n = 7
    r = 0x1b
    result = gf2nMul(a, b, n, r)
    print "0x%x" % result

