def fib():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

def trib():
    a, b , c = 0, 1, 1
    while True:
        yield a
        a, b, c = b, c, a + b + c

