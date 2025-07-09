#!/usr/bin/python

import imageio
import matplotlib.pyplot as plt
import numpy as np

# 16, 50 - 3233, 1456

# some x positions of leftmost 1 pixel
# 17, 118, 163, 291, 675, 1096, 2650, 3225
xpos = np.array([
    (0, 17),
    (1, 26),
    (2, 35),
    (3, 44),
    (5, 63),
    (8, 90),
    (12, 118),
])

CHW = 9.14
CHH = 22

# img = imageio.imread("img/mk51_rom_dump_screen.png")
# raw = decode(img)

def decode(img):
    res = []

    for i in range(64):
        line = []
        for j in range(22 * 16):
            x0 = int(16 + CHW * j)
            y0 = 50 + CHH * i
            n = np.sum(img[y0:y0 + CHH, x0:x0 + int(CHW), 0])
            line.append(n > 44250)
        res.append(line)
    return np.array(res).astype(int)

            
# a: 0-7
# b: 0-7
# c: 0-21
# d: 0-15
def getbit(raw, a, b, c, d):
    return raw[a * 8 + b, c * 16 + d]

def mcode_info(m):
    def f(a, b):
        res = ""
        r = range(a, b + 1) if a <= b else range(a, b - 1, -1)
        for i in r:
            res += str(m[i])
        return res
    return (f"m19-21:{f(19,21)} m14-18:{f(14,18)} m10-13:{f(10,13)} "
            f"m10-13,19-21:{f(10,13)}{f(19,21)} m3-9:{f(3,9)} m2-0:{f(2,0)}")

def reorder(raw):
    for d in range(16):
        for a in range(8):
            for b in range(8):
                m = []
                for c in range(22):
                    m.append(getbit(raw, a ^ 7, b, c, d))
                    #print(getbit(raw, a, b, c, d), end="")
                m = np.array(m)
                print(f"{d:x}{a:x}{b:x} {mcode_info(m)}")
            print()

def reorder2(raw):
    for a in range(8):
        for b in range(8):
            for d in range(16):
                m = []
                for c in range(22):
                    m.append(getbit(raw, a ^ 7, b, c, d))
                    #print(getbit(raw, a, b, c, d), end="")
                m = np.array(m)
                print(f"{d:x}{a:x}{b:x} {mcode_info(m)}")
            print()

def subw(m, a, b):
    res = ""
    r = range(a, b + 1) if a <= b else range(a, b - 1, -1)
    for i in r:
        res += str(m[i])
    return res

def print_adr(raw):
    for d in range(16):
        for a in range(8):
            for b in range(8):
                m = []
                for c in range(22):
                    m.append(getbit(raw, a ^ 7, b ^ 7, c, d))
                    #print(getbit(raw, a, b, c, d), end="")
                m = np.array(m)
                print(f"{d:04b} {a:03b} {b:03b}: {subw(m, 9, 6)} {subw(m, 2, 0)} {subw(m, 5, 5)}{subw(m, 4, 3)} "
                      f"{int(subw(m, 9, 6), 2):2d} {int(subw(m, 9, 6), 2) ^ 15:2d} "
                      f"{int(subw(m, 6, 9), 2):2d} {int(subw(m, 6, 9), 2) ^ 15:2d}")
            print()

def print_const1(raw):
    def num(arr):
        digits = [str(1 - d) for d in arr]
        return int("".join(reversed(digits)), 2)

    for d in range(16):
        for a in range(8):
            for b in range(8):
                m = []
                for c in range(22):
                    m.append(getbit(raw, a ^ 7, b, c, d))
                m = np.array(m)
                if not np.all(m[14:19] == [1, 0, 1, 1, 1]): continue
                print(f"{d:x}{a:x}{b:x} {mcode_info(m)} ({num(m[3:10]):02d})")

def print_for_entry_points(raw):
    def num(arr):
        digits = [str(1 - d) for d in arr]
        return int("".join(reversed(digits)), 2)

    for a in range(8):
        for d in range(16):
            for b in range(8):
                m = []
                for c in range(22):
                    m.append(getbit(raw, a ^ 7, b, c, d))
                m = np.array(m)
                print(f"{d:x}{a:x}{b:x} {mcode_info(m)} ({num(m[3:10]):02d})")
            print()


def load_microcode():
    return decode(imageio.imread("img/mk51_rom_dump_screen.png"))


class Microcode:
    def __init__(self, raw):
        self._raw = raw

    def get(self, adr):
        a = adr // 16
        b = adr % 16
        bits = self._raw[a, b::16]
        assert len(bits) == 22
        bits = 1 - bits
        return np.sum(np.left_shift(1, np.mgrid[0:22]) * bits)

def mcode_cmd_info(cmd):
    m = np.where(np.left_shift(1, np.mgrid[0:22]) & cmd, 1, 0)
    def f(a, b):
        res = ""
        r = range(a, b + 1) if a <= b else range(a, b - 1, -1)
        for i in r:
            res += str(m[i])
        return res
    return (f"m19-21:{f(19,21)} m14-18:{f(14,18)} m10-13:{f(10,13)} "
            f"m10-13,19-21:{f(10,13)}{f(19,21)} m3-9:{f(3,9)} m2-0:{f(2,0)}")


def bf(n, a, b):
    return (n >> b) & ((1 << (a - b + 1)) - 1)

def inst_field(cmd):
    return (cmd >> 14) & 0x1f

def is_call(cmd):
    return inst_field(cmd) == 0x1

def is_return(cmd):
    return inst_field(cmd) == 0x3

def is_const(cmd):
    return inst_field(cmd) == 0x2

def return_adr(adr, cmd):
    return (bf(cmd, 2, 0) << 7) | (bf(cmd, 21, 19) << 4) | bf(cmd, 13, 10)

def imm_next_adr(adr, cmd):
    n = ((cmd & 7) << 7) | (((cmd >> 3) & 7) << 4)
    # TODO: analyze it better, when is this field a constant and when addr?
    if (inst_field(cmd) & 0x18) == 8:
        n |= (cmd >> 6) & 0xf
    else:
        n |= adr & 0xf
    return n

def next_adr(adr, cmd):
    if is_call(cmd):
        return return_adr(adr, cmd)
    return imm_next_adr(adr, cmd)

def decode_instr(adr, cmd):
    if is_call(cmd):
        return f"CALL {imm_next_adr(adr, cmd):04x}"
    if is_return(cmd):
        return "RETURN"
    if is_const(cmd):
        return f"CONST {bf(cmd, 9, 6)}"
    return ""

def print_microcode(mc):
    for i in range(16 * 64):
        cmd = mc.get(i)
        print(f"{i:03x} {cmd:022b} {next_adr(i, cmd):03x} {mcode_cmd_info(cmd)}")

def print_cmd_info(adr, cmd):
    di = decode_instr(adr, cmd)
    if not di: di = "???"
    print(f"{adr:03x}: {di:15s} n:{next_adr(adr, cmd):03x}")
    print(f"                     ins:{bf(cmd, 18, 14):05b} "
          f"reg/stc:{bf(cmd, 21, 19):01x} "
          f"w/str:{bf(cmd, 13, 10):01x} ac1:{bf(cmd, 2, 0):01x} "
          f"ac0:{bf(cmd, 5, 3):01x} ar/imm:{bf(cmd, 9, 6)}")

def microcode_paths(mc):
    def refs_info(ind, r):
        if ind < 2:
            return ""
        return "(from " + ",".join([f"{a:03x}" for a in r]) + ")"

    n = 16 * 64
    indeg = np.zeros((n,), dtype=int)
    refs = {}
    for i in range(n):
        cmd = mc.get(i)
        na = next_adr(i, cmd)
        indeg[na] += 1
        refs.setdefault(na, []).append(i)

    done = np.zeros((n,), dtype=bool)
    while True:
        for i in range(n):
            if not done[i] and indeg[i] == 0:
                break
        else:
            break
        while not done[i]:
            done[i] = True
            cmd = mc.get(i)
            next = next_adr(i, cmd)
            print_cmd_info(i, cmd)
            ri = refs_info(indeg[i], refs.get(i, []))
            if ri:
                print(" " * 21 + ri)
            i = next
        print()
