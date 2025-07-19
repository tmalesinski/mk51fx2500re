#!/usr/bin/python

import imageio
import matplotlib.pyplot as plt
import numpy as np
from windows import decode_window

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

def bit(n, a):
    return (n >> a) & 1

def inst_field(cmd):
    return (cmd >> 14) & 0x1f

def is_call(cmd):
    return inst_field(cmd) == 0x1

def is_return(cmd):
    return inst_field(cmd) == 0x3

def is_const(cmd):
    return inst_field(cmd) == 0x2

# ALU input 0: masked selected shift reg or KR0
def dins0(cmd):
    return bf(cmd, 18, 15) == 3

# ALU input 0: imm on the first window position
def dins1(cmd):
    return bf(cmd, 18, 14) == 2

# ALU input 0: selected shift reg but only on some windows
# ALU input 1: dins4 (window and some shift fixed reg?)
def dins2(cmd):
    return bf(cmd, 18, 14) == 0xd

# ALU input 0: selected shift reg (with particular MCD 17 and MCD 18)
# ALU input 1: KEY (wih particular MCD17 and MCD 18)
def dins3(cmd):
    return bf(cmd, 15, 14) != 1

# Enable window (otherwise finish instruction on the next digit)
def dins10(cmd):
    return not (bf(cmd, 18, 16) == 0 and bf(cmd, 15, 14) != 2)

# Probably to display buffer, depends on ALU input 0
def dins11(cmd):
    return not (bf(cmd, 17, 14) == 5)

# Some ALU control, maybe add/sub?
def dins12(cmd):
    return not (bf(cmd, 15, 14) == 1 or not bit(cmd, 16))

# Likely write enable for shift registers
def dins13(cmd):
    int1 = bf(cmd, 18, 17) == 0 or bit(cmd, 15)
    int2 = bf(cmd, 15, 14) != 2
    return not (int1 and int2)

# To shift reg routing, depends on ALU input 0, so maybe some alternative
# value to insert. Maybe shifting with insertion.
def dins14(cmd):
    return bf(cmd, 18, 14) == 0x1d or bf(cmd, 18, 14) == 5

# dins15: some alu logic

def alu_input1(cmd):
    res = []
    imm = f"#{bf(cmd, 9, 6):x}"
    selr = f"R{bf(cmd, 21, 19)}"
    if bit(cmd, 18):
        res.append("R1" if bit(cmd, 17) else "R0")
    if not bit(cmd, 18) and bit(cmd, 17):
        if bf(cmd, 9, 6) == 0 and dins3(cmd):
            res.append("KEY")
        if bf(cmd, 9, 6) != 0:
            res.append(f"{imm}&WIN")
    if dins2(cmd):
        res.append(f"{selr}&?(mcd)")
    if not res:
        res.append("0")
    return ",".join(res)

def alu_input0(cmd):
    imm = f"#{bf(cmd, 9, 6):x}"
    selr = f"R{bf(cmd, 21, 19)}"
    res = []
    if bf(cmd, 18, 17) != 0 and dins3(cmd):
        res.append(selr)
    if dins0(cmd) and bf(cmd, 9, 6) == 0:
        res.append("KR0?")
    if dins0(cmd) and bf(cmd, 9, 6) != 0:
        res.append(f"{selr}&{imm}")
    if dins1(cmd):
        res.append(f"{imm}&WIN")
    if dins2(cmd):
        res.append("DINS4")
    if not res:
        res.append("0")
    return ",".join(res)


def has_next_row(cmd):
    return (bf(cmd, 18, 17) != 1 and bf(cmd, 18, 14) != 2 and
            bf(cmd, 18, 15) != 3)

def return_adr(adr, cmd, ret_c1s=None):
    rc1 = bf(cmd, 2, 0)
    if ret_c1s is not None:
        r = ret_c1s.get(imm_next_adr(adr, cmd), None)
        if r is not None:
            rc1 = r
    return (rc1 << 7) | (bf(cmd, 21, 19) << 4) | bf(cmd, 13, 10)

def imm_next_adr(adr, cmd):
    n = ((cmd & 7) << 7) | (((cmd >> 3) & 7) << 4)
    if has_next_row(cmd):
        n |= (cmd >> 6) & 0xf
    else:
        n |= adr & 0xf
    return n

def is_branch_z(cmd):
    return bf(cmd, 16, 15) == 3 and ((bf(cmd, 18, 14) & 0x19) != 0)

def branch_z_adr(adr, cmd):
    if not is_branch_z(cmd): return None
    return next_adr(adr, cmd) | 0x20

def is_branch_c(cmd):
    return bit(cmd, 15)

def branch_c_adr(adr, cmd):
    if not is_branch_c(cmd): return None
    return next_adr(adr, cmd) | 0x10

def next_adr(adr, cmd, ret_c1s=None):
    if is_call(cmd):
        return return_adr(adr, cmd, ret_c1s)
    return imm_next_adr(adr, cmd)

def decode_main_instr(adr, cmd):
    if is_call(cmd):
        return f"CALL {imm_next_adr(adr, cmd):04x}"
    if is_return(cmd):
        return "RETURN"
    sub = dins12(cmd)
    a0 = alu_input0(cmd)
    a1 = alu_input1(cmd)
    if dins13(cmd):  # we
        dest = f"R{bf(cmd, 21, 19)}"
        a0_is_dest = a0 == dest
        if a1 == "0":
            if a0 == "0":
                return f"CLR {dest}"
            else:
                return f"MOV {a0},{dest}"
        elif a0 == "0":
            if not sub:
                return f"MOV {a1},{dest}"
        else:
            op = "SUB" if sub else "ADD"
            if a0_is_dest:
                return f"{op} {a1},{dest}"
            else:
                return f"{op} {a0},{a1},{dest}"
    else:  # not we
        if a0 == "0" and a1 == "0":
            return f"NOP{bf(cmd, 18, 14)}"
        elif sub:
            return f"CMP {a1},{a0}"
        else:
            return f"CMPN {a1},{a0}"
    return "???"


def decode_instr(adr, cmd):
    i = decode_main_instr(adr, cmd)
    if dins10(cmd):
        i += f" W{decode_window(bf(cmd, 13, 10))}"
    bca = branch_c_adr(adr, cmd)
    na = next_adr(adr, cmd)
    if bca is not None and bca != na:
        i += f" BC:{bca:03x}"
    bza = branch_z_adr(adr, cmd)
    if bza is not None and bza != na:
        i += f" BZ:{bza:03x}"
    if not dins11(cmd):
        i += " DSP?"
    if dins14(cmd):
        i += " SH?"
    return i


def print_microcode(mc):
    for i in range(16 * 64):
        cmd = mc.get(i)
        print(f"{i:03x} {cmd:022b} {next_adr(i, cmd):03x} {mcode_cmd_info(cmd)}")

def print_cmd_info(adr, cmd):
    di = decode_instr(adr, cmd)
    if not di: di = "???"
    na = next_adr(adr, cmd)
    print(f"{adr:03x}: {di:15s}")
    print(f"                     n:{na:03x} "
          f"alu0: {alu_input0(cmd):7s} alu1: {alu_input1(cmd):7s}")
    print(f"                     ins:{bf(cmd, 18, 14):05b} "
          f"reg/stc:{bf(cmd, 21, 19):01x} "
          f"w/str:{bf(cmd, 13, 10):01x} ac1:{bf(cmd, 2, 0):01x} "
          f"ac0:{bf(cmd, 5, 3):01x} ar/imm:{bf(cmd, 9, 6)} "
          f"we:{int(dins13(cmd))}")
    branches = []
    bca = branch_c_adr(adr, cmd)
    if bca is not None and bca != na:
        branches.append(f"bc:{bca:03x}")
    bza = branch_z_adr(adr, cmd)
    if bza is not None and bza != na:
        branches.append(f"bz:{bza:03x}")
    if branches:
        print(f"                     {' '.join(branches)}")

def microcode_paths(mc):
    ret_c1s = call_return_c1s(mc)
    def refs_info(ind, r):
        if ind < 2:
            return ""
        return "(from " + ",".join([f"{a:03x}" for a in r]) + ")"

    n = 16 * 64
    indeg = np.zeros((n,), dtype=int)
    refs = {}
    for i in range(n):
        cmd = mc.get(i)
        na = next_adr(i, cmd, ret_c1s)
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
            next = next_adr(i, cmd, ret_c1s)
            print_cmd_info(i, cmd)
            ri = refs_info(indeg[i], refs.get(i, []))
            if ri:
                print(" " * 21 + ri)
            i = next
        print()

def instruction_table():
    for instr in range(32):
        cmd = (instr << 14) | (5 << 19) | (3 << 6)
        print(f"{instr:05b} "
              f"{alu_input0(cmd):10s} {alu_input1(cmd):10s} "
              f"rowadr:{int(has_next_row(cmd))} "
              f"we: {int(dins13(cmd))} "
              f"sub: {int(dins12(cmd))} "
              f"brz: {int(is_branch_z(cmd))} "
              f"brc: {int(is_branch_c(cmd))} "
              f"call: {int(is_call(cmd))} "
              f"ret: {int(is_return(cmd))} "
              f"di11: {int(dins11(cmd))} "
              f"di14: {int(dins14(cmd))} "
              f"di0: {int(dins0(cmd))} "
              f"di1: {int(dins1(cmd))} "
              f"di2: {int(dins2(cmd))} "
              f"di3: {int(dins3(cmd))} "
              f"di10: {int(dins10(cmd))}")

        print(decode_instr(0, cmd))

def call_return_c1s(mc):
    searching = set()
    ret_c1s = {}

    def do_find_return(a):
        stack = [a]
        visited = set()
        returns = set()
        while stack:
            a = stack.pop()
            if a in visited: continue
            visited.add(a)
            cmd = mc.get(a)
            if is_return(cmd):
                returns.add(bf(cmd, 2, 0))
                continue
            if is_call(cmd):
                ca = imm_next_adr(a, cmd)
                if ca not in ret_c1s:
                    print(f"  recursive search for {ca:03x}")
                    find_return(ca)
                rc1 = ret_c1s.get(ca, None)
                if rc1 is not None:
                    na = (rc1 << 7) | (bf(cmd, 21, 19) << 4) | bf(cmd, 13, 10)
                else:
                    print(f"  {ca:03x} ???")
                    # TODO: this should be an error when we detect impossible branches
                    # return None
                    continue
            else:
                na = next_adr(a, cmd)
            stack.append(na)
            # TODO: detect impossible branches
            if is_branch_z(cmd):
                stack.append(branch_z_adr(a, cmd))
            if is_branch_c(cmd):
                stack.append(branch_c_adr(a, cmd))
        print(f"Num of returns: {len(returns)}")
        if len(returns) == 1:
            return returns.pop()
        else:
            return None

    def find_return(a):
        if a in ret_c1s:
            return ret_c1s[a]
        if a in searching:
            print(f"  recursion loop with {a:03x}")
            return None
        searching.add(a)
        try:
            r = do_find_return(a)
            if r is not None:
                print(f"  call {a:03x} -> {r << 7:03x}")
            ret_c1s[a] = r
        finally:
            searching.remove(a)
        return r

    for a in range(0x400):
        cmd = mc.get(a)
        if is_call(cmd):
            ca = imm_next_adr(a, cmd)
            if ca not in ret_c1s:
                r = find_return(ca)
                if r:
                    ret_c1s[ca] = r
                    print(f"{ca:03x} -> {r << 7:03x}")
                else:
                    print(f"{ca:03x} not found")
    return ret_c1s
