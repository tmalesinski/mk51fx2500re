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
