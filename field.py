def bit(n, a):
    return (n >> a) & 1

def expand_bits(n, nb):
    return [bit(n, i) for i in range(nb)]

def lsfr_next(n):
    next_bit = ((bit(n, 3) and not bit(n, 2)) or
                (not bit(n, 3) and bit(n, 2)) or
                (not bit(n, 2) and not bit(n, 1) and not bit(n, 0)))
    return ((n << 1) & 0xf) | (1 if next_bit else 0)

def print_cycle():
    n = 0
    for i in range(20):
        print(f"{n:x} {n:04b}")
        n = lsfr_next(n)


def get_cycle():
    res = []
    n = 12
    for i in range(15):
        res.append(n)
        n = lsfr_next(n)
    return res

def wnd1(w, dc):
    mcd = expand_bits(w << 10, 14)
    dc = expand_bits(dc, 4)
    return not ((mcd[13] and mcd[11] and
                 dc[0] and dc[1] and dc[2] and not dc[3]) or
                (mcd[13] and not mcd[11] and not mcd[10] and
                 not dc[0] and not dc[1] and not dc[2] and dc[3]) or
                (not mcd[11] and mcd[10] and
                 dc[0] and dc[1] and dc[2] and dc[3]) or
                (not mcd[13] and mcd[12] and not mcd[11] and not mcd[10] and
                 not dc[0] and dc[1] and dc[2] and dc[3]))

def wnd2(w, dc):
    mcd = expand_bits(w << 10, 14)
    dc = expand_bits(dc, 4)
    return not ((mcd[13] and mcd[10] and
                 dc[0] and not dc[1] and not dc[2] and not dc[3]) or
                (mcd[13] and not mcd[10] and
                 not dc[0] and not dc[1] and dc[2] and dc[3]) or
                (not mcd[13] and mcd[12] and not mcd[11] and
                 not dc[0] and not dc[1] and dc[2] and dc[3]))

def wnd3(w, dc):
    mcd = expand_bits(w << 10, 14)
    dc = expand_bits(dc, 4)
    return not ((not mcd[13] and mcd[12] and mcd[11] and mcd[10] and
                 dc[0] and dc[1] and not dc[2] and dc[3]) or
                (not mcd[13] and mcd[12] and mcd[11] and not mcd[10] and
                 not dc[0] and dc[1] and dc[2] and dc[3]) or
                (not mcd[13] and not mcd[12] and mcd[11] and mcd[10] and
                 dc[0] and not dc[1] and not dc[2] and not dc[3]))

def wnd4(w, dc):
    mcd = expand_bits(w << 10, 14)
    dc = expand_bits(dc, 4)
    return not ((not mcd[13] and not mcd[12] and mcd[11] and not mcd[10] and
                 dc[0] and dc[1] and dc[2] and not dc[3]) or
                (not mcd[13] and not mcd[12] and not mcd[11] and mcd[10] and
                 dc[0] and dc[1] and dc[2] and dc[3]) or
                (not mcd[13] and not mcd[12] and not mcd[11] and not mcd[10] and
                 not dc[0] and not dc[1] and dc[2] and dc[3]))

def to01(b):
    return 1 if b else 0

def print_window_signals():
    cycle = get_cycle()
    for w in range(16):
        print(f"w={w:x}")
        for wf in [wnd4, wnd3, wnd2, wnd1]:
            for dc in cycle:
                print(to01(wf(w, dc)), end="")
            print()

        r0l = []
        r1l = []
        r0 = False
        r1 = True
        for dc in cycle:
            r0l.append(r0)
            r1l.append(r1)
            wnd234 = not (wnd2(w, dc) and wnd3(w, dc) and wnd4(w, dc))
            wnd134 = not (wnd1(w, dc) and wnd3(w, dc) and wnd4(w, dc))
            r1 = ((not (r1 and wnd234)) and (r0 or r1))
            r0 = wnd134
        print()
        for r0 in r0l:
            print(to01(r0), end="")
        print()
        for r1 in r1l:
            print(to01(r1), end="")
        print()

def decode_window(w):
    start = stop = None
    for i, dc in enumerate(get_cycle()):
        wstart = not (wnd2(w, dc) and wnd3(w, dc) and wnd4(w, dc))
        wstop = not (wnd1(w, dc) and wnd3(w, dc) and wnd4(w, dc))
        if wstart: start = i
        if wstop: stop = i
    return start, stop

# TODO: for w=0xc ([1:0]) there is probably no adjustment on 1
# (possibly to have exponents in -159 to 159)
def has_decimal_adjustment(w):
    return w & 0xc == 0xc
