def bf(n, a, b):
    return (n >> b) & ((1 << (a - b + 1)) - 1)

def bit(n, a):
    return (n >> a) & 1
