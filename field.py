from bits import bit

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

def fld1(f, dc):
    mcd = expand_bits(f << 10, 14)
    dc = expand_bits(dc, 4)
    return not ((mcd[13] and mcd[11] and
                 dc[0] and dc[1] and dc[2] and not dc[3]) or
                (mcd[13] and not mcd[11] and not mcd[10] and
                 not dc[0] and not dc[1] and not dc[2] and dc[3]) or
                (not mcd[11] and mcd[10] and
                 dc[0] and dc[1] and dc[2] and dc[3]) or
                (not mcd[13] and mcd[12] and not mcd[11] and not mcd[10] and
                 not dc[0] and dc[1] and dc[2] and dc[3]))

def fld2(f, dc):
    mcd = expand_bits(f << 10, 14)
    dc = expand_bits(dc, 4)
    return not ((mcd[13] and mcd[10] and
                 dc[0] and not dc[1] and not dc[2] and not dc[3]) or
                (mcd[13] and not mcd[10] and
                 not dc[0] and not dc[1] and dc[2] and dc[3]) or
                (not mcd[13] and mcd[12] and not mcd[11] and
                 not dc[0] and not dc[1] and dc[2] and dc[3]))

def fld3(f, dc):
    mcd = expand_bits(f << 10, 14)
    dc = expand_bits(dc, 4)
    return not ((not mcd[13] and mcd[12] and mcd[11] and mcd[10] and
                 dc[0] and dc[1] and not dc[2] and dc[3]) or
                (not mcd[13] and mcd[12] and mcd[11] and not mcd[10] and
                 not dc[0] and dc[1] and dc[2] and dc[3]) or
                (not mcd[13] and not mcd[12] and mcd[11] and mcd[10] and
                 dc[0] and not dc[1] and not dc[2] and not dc[3]))

def fld4(f, dc):
    mcd = expand_bits(f << 10, 14)
    dc = expand_bits(dc, 4)
    return not ((not mcd[13] and not mcd[12] and mcd[11] and not mcd[10] and
                 dc[0] and dc[1] and dc[2] and not dc[3]) or
                (not mcd[13] and not mcd[12] and not mcd[11] and mcd[10] and
                 dc[0] and dc[1] and dc[2] and dc[3]) or
                (not mcd[13] and not mcd[12] and not mcd[11] and not mcd[10] and
                 not dc[0] and not dc[1] and dc[2] and dc[3]))

def print_field_signals():
    cycle = get_cycle()
    for f in range(16):
        print(f"f={f:x}")
        for ff in [fld4, fld3, fld2, fld1]:
            for dc in cycle:
                print(int(ff(f, dc)), end="")
            print()

        r0l = []
        r1l = []
        r0 = False
        r1 = True
        for dc in cycle:
            r0l.append(r0)
            r1l.append(r1)
            fld234 = not (fld2(f, dc) and fld3(f, dc) and fld4(f, dc))
            fld134 = not (fld1(f, dc) and fld3(f, dc) and fld4(f, dc))
            r1 = ((not (r1 and fld234)) and (r0 or r1))
            r0 = fld134
        print()
        for r0 in r0l:
            print(int(r0), end="")
        print()
        for r1 in r1l:
            print(int(r1), end="")
        print()

def compute_decoded_field(f):
    start = stop = None
    for i, dc in enumerate(get_cycle()):
        fstart = not (fld2(f, dc) and fld3(f, dc) and fld4(f, dc))
        fstop = not (fld1(f, dc) and fld3(f, dc) and fld4(f, dc))
        if fstart: start = i
        if fstop: stop = i
    return start, stop

_FIELDS = None

def init_fields():
    global _FIELDS
    if not _FIELDS:
        _FIELDS = [compute_decoded_field(f) for f in range(16)]

def decode_field(f):
    init_fields()
    return _FIELDS[f]

# TODO: for f=0xc ([1:0]) there is probably no adjustment on 1
# (possibly to have exponents in -159 to 159)
def has_decimal_adjustment(f):
    return f & 0xc == 0xc
