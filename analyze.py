#!/usr/bin/python

import imageio
import matplotlib.pyplot as plt
import numpy as np

from bits import *
from instr import *
from windows import decode_window, has_decimal_adjustment

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


def load_microcode_from_txt():
    res = []
    with open("mk51dump.txt") as f:
        for line in f.readlines():
            res.append(np.array(list(line.strip())) != "0")
    return np.array(res).astype(int)


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


# TODO: delete
def cons_adr(colh, coll, row):
    return make_adr(colh, coll, row)

# ALU input 0: masked selected shift reg or KR0
def dins0(cmd):
    return bf(cmd, 18, 15) == 3

# ALU input 0: imm on the last window position
def dins1(cmd):
    return bf(cmd, 18, 14) == 2

# ALU input 0: selected shift reg but only on some windows
# ALU input 1: dins4 (delayed selected reg when in window)
def dins2(cmd):
    return bf(cmd, 18, 14) == 0xd

# ALU input 0: selected shift reg (with particular MCD 17 and MCD 18)
# ALU input 1: KEY (wih particular MCD17 and MCD 18)
def dins3(cmd):
    return bf(cmd, 15, 14) != 1

# Enable window (otherwise finish instruction on the next digit)
def dins10(cmd):
    return not (bf(cmd, 18, 16) == 0 and bf(cmd, 15, 14) != 2)

# Swap R0 with the selected one.
def dins11(cmd):
    return not (bf(cmd, 17, 14) == 5)

# Add/sub.
def dins12(cmd):
    return not (bf(cmd, 15, 14) == 1 or not bit(cmd, 16))

def is_sub(cmd):
    return dins12(cmd)

# Likely write enable for shift registers
def dins13(cmd):
    int1 = bf(cmd, 18, 17) == 0 or bit(cmd, 15)
    int2 = bf(cmd, 15, 14) != 2
    return not (int1 and int2)

# Swap R1 with the selected one.
def dins14(cmd):
    return bf(cmd, 18, 14) == 0x1d or bf(cmd, 18, 14) == 4

# dins15: selected reg when constant, added past ALU so that the register
# gets shifted

class AluInput:
    def __str__(self):
        raise NotImplementedError()

    def always_zero(self):
        return False

class RegisterInput(AluInput):
    def __init__(self, n):
        self.n = n

    def __str__(self):
        return f"R{self.n}"

class KeyCodeInput(AluInput):
    def __str__(self):
        return f"KEY"

class ConstantInput(AluInput):
    def __init__(self, n):
        self.n = n

    def __str__(self):
        return "0" if self.n == 0 else f"#{self.n:x}.L"

    def always_zero(self):
        return self.n == 0

class Kr0Input(AluInput):
    def __str__(self):
        return "KR0?"

class MaskedRegisterInput(AluInput):
    def __init__(self, n, mask):
        self.n = n
        self.mask = mask

    def __str__(self):
        return f"R{self.n}&#{self.mask:x}"

    def always_zero(self):
        return self.mask == 0

class OredRegisterInput(AluInput):
    def __init__(self, n, mask):
        self.n = n
        self.mask = mask

    def __str__(self):
        return f"#{self.mask:x}.L|R{self.n}"

class PushDigitInput(AluInput):
    def __init__(self, n, digit):
        self.n = n
        self.digit = digit

    def __str__(self):
        return f"#{self.digit:x}.H|(R{self.n} SHR)"

class LeftShiftedRegisterInput(AluInput):
    def __init__(self, n):
        self.n = n

    def __str__(self):
        return f"R{self.n} SHL"


def alu_input1_structured(cmd):
    res = []
    if bit(cmd, 18):
        res.append(RegisterInput(1 if bit(cmd, 17) else 0))
    if not bit(cmd, 18) and bit(cmd, 17):
        if bf(cmd, 9, 6) == 0 and dins3(cmd):
            res.append(KeyCodeInput())
        if bf(cmd, 9, 6) != 0:
            res.append(ConstantInput(bf(cmd, 9, 6)))
    if dins2(cmd):
        if not bit(cmd, 13) and (not bit(cmd, 12) or bit(cmd, 11)):
            # TODO: does it only happen with one element fields and
            # is it then or with an immediate?
            res.append(RegisterInput(bf(cmd, 21, 19)))
    if not res:
        res.append(ConstantInput(0))
    if len(res) == 2:
        if (isinstance(res[0], ConstantInput) and
            isinstance(res[1], RegisterInput)):
            res = [OredRegisterInput(res[1].n, res[0].n)]
    assert len(res) == 1, res
    return res[0]


def alu_input1_old(cmd):
    res = []
    imm = f"#{bf(cmd, 9, 6):x}"
    selr = f"R{bf(cmd, 21, 19)}"
    if bit(cmd, 18):
        res.append("R1" if bit(cmd, 17) else "R0")
    if not bit(cmd, 18) and bit(cmd, 17):
        if bf(cmd, 9, 6) == 0 and dins3(cmd):
            res.append("KEY")
        if bf(cmd, 9, 6) != 0:
            res.append(f"{imm}.L")
    if dins2(cmd):
        if not bit(cmd, 13) and (not bit(cmd, 12) or bit(cmd, 11)):
            # TODO: does it only happen with one element fields and
            # is it then or with an immediate?
            res.append(f"{selr}")
    if not res:
        res.append("0")
    return "|".join(res)

def alu_input1(cmd):
    old_res = alu_input1_old(cmd)
    new_res = str(alu_input1_structured(cmd))
    if old_res != new_res:
        print(f"{old_res}   !=   {new_res}")
    return old_res

def alu_input0_structured(cmd):
    imm = bf(cmd, 9, 6)
    selr = bf(cmd, 21, 19)
    res = []
    if bf(cmd, 18, 17) != 0 and dins3(cmd):
        res.append(RegisterInput(selr))
    if dins0(cmd) and bf(cmd, 9, 6) == 0:
        res.append(Kr0Input())
    if dins0(cmd) and bf(cmd, 9, 6) != 0:
        res.append(MaskedRegisterInput(selr, imm))
    if dins1(cmd):
        res.append(PushDigitInput(selr, imm))
    if dins2(cmd):
        w = decode_window(bf(cmd, 13, 10))
        if w[0] == w[1]:
            res.append(ConstantInput(0))
        else:
            res.append(LeftShiftedRegisterInput(selr))
    if not res:
        res.append(ConstantInput(0))
    assert len(res) == 1
    return res[0]

def alu_input0_old(cmd):
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
        res.append(f"{imm}.H|({selr} SHR)")
    if dins2(cmd):
        w = decode_window(bf(cmd, 13, 10))
        if w[0] == w[1]:
            res.append("0")
        else:
            res.append(f"{selr} SHL")
    if not res:
        res.append("0")
    return ",".join(res)


def alu_input0(cmd):
    old_res = alu_input0_old(cmd)
    new_res = str(alu_input0_structured(cmd))
    if old_res != new_res:
        print(f"{old_res}   !=   {new_res}")
    return old_res


def has_next_row(cmd):
    return (bf(cmd, 18, 17) != 1 and bf(cmd, 18, 14) != 2 and
            bf(cmd, 18, 15) != 3)

# TODO: stop using, it does not check ret_cols
def return_adr(adr, cmd):
    rcol = cons_adr(instr_next_colh(cmd), 0, 0)
    return rcol | (bf(cmd, 21, 19) << 4) | bf(cmd, 13, 10)

def return_adrs(adr, cmd, ret_cols=None):
    # TODO: fail on missing returns instead of this guess?
    rcols = [(cons_adr(instr_next_colh(cmd), 0, 0), "")]
    if ret_cols is not None:
        rs = ret_cols.get(imm_next_adr(adr, cmd), None)
        if rs is not None:
            rcols = rs
    padr = (bf(cmd, 21, 19) << 4) | bf(cmd, 13, 10)
    return [(r | padr, l) for r, l in rcols]

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
    return bit(cmd, 15) and not is_return(cmd)

def branch_c_adr(adr, cmd):
    if not is_branch_c(cmd): return None
    return next_adr(adr, cmd) | 0x10

def branch_c_possible(cmd):
    a0 = alu_input0_structured(cmd)
    a1 = alu_input1_structured(cmd)
    # TODO: seems wrong on sub with a0 == 0 (if it happens at all)
    return not a0.always_zero() and not a1.always_zero()

# TODO: stop using, it does not use ret_cols for calls.
def next_adr(adr, cmd):
    if is_call(cmd):
        return return_adr(adr, cmd)
    if is_return(cmd):
        return None
    return imm_next_adr(adr, cmd)

def cz_possible(cmd, c, z):
    if c is None:
        return cz_possible(cmd, True, z) or cz_possible(cmd, False, z)
    if z is None:
        return cz_possible(cmd, c, True) or cz_possible(cmd, c, False)
    if c and alu_input1_structured(cmd).always_zero():
        return False
    if c and z and is_sub(cmd):
        return False
    # TODO: any other interesting cases?
    return True

def all_same(lst):
    if len(lst) == 0: return True
    for elt in lst[1:]:
        if elt != lst[0]: return False
    return True

def merge_edges(edges):
    for i in range(2):
        for v in [True, False]:
            sel = [e[2] for e in edges if e[i] == v]
            if len(sel) != 2: continue
            if not all_same(sel): continue

            edges1 = [e for e in edges if e[i] != v]
            merged = [None, None, sel[0]]
            merged[i] = v
            edges1.append(tuple(merged))
            edges = edges1
    return edges

def simplify_edges(edges):
    res = []
    for e in edges:
        for i in range(2):
            if e[i] is None: continue
            n = 0
            for e1 in edges:
                if e1[i] == e[i]: n += 1
            if n != 1: continue
            simpler = list(e)
            simpler[1 - i] = None
            res.append(tuple(simpler))
            break
        else:
            res.append(e)
    return res

def explain_edges(adr, cmd, edges):
    d = decode_main_instr(adr, cmd)
    tr = {}
    if d.startswith("CMP "):
        tr = {
            "C": ">",
            "!C": "<=",
            "Z": "=",
            "!Z": "!=",
            "!C!Z": "<",
        }
    elif d.startswith("CMPN "):
        tr = {
            "C": "<=",
            "!C": ">",
        }
    return [(e[0], tr.get(e[1], e[1])) for e in edges]

def outgoing_edges(adr, cmd, ret_cols):
    if is_call(cmd):
        return return_adrs(adr, cmd, ret_cols)
    if is_return(cmd):
        return []
    na = imm_next_adr(adr, cmd)
    c_enabled = is_branch_c(cmd) and na & 0x10 == 0
    z_enabled = is_branch_z(cmd) and na & 0x20 == 0
    edges = []
    for c in [True, False] if c_enabled else [None]:
        for z in [True, False] if z_enabled else [None]:
            if not cz_possible(cmd, c, z):
                continue
            a = na
            if is_branch_c(cmd) and c:
                a |= 0x10
            if is_branch_z(cmd) and not z:
                a |= 0x20
            edges.append((c, z, a))

    if all_same([e[2] for e in edges]):
        return [(edges[0][2], "")]
    edges = simplify_edges(merge_edges(edges))

    res = []
    for e in edges:
        cstr = ""
        if e[0] is True:
            cstr += "C"
        if e[0] is False:
            cstr += "!C"
        if e[1] is True:
            cstr += "Z"
        if e[1] is False:
            cstr += "!Z"
        res.append((e[2], cstr))

    return explain_edges(adr, cmd, res)

def decode_main_instr(adr, cmd):
    if is_jump(cmd):
        return f"JUMP {imm_next_adr(adr, cmd):03x}"
    if is_call(cmd):
        return f"CALL {imm_next_adr(adr, cmd):03x}"
    if is_return(cmd):
        return f"RETURN {imm_next_adr(adr, cmd):03x}"
    sub = dins12(cmd)
    a0 = alu_input0(cmd)
    a0s = alu_input0_structured(cmd)
    a1 = alu_input1(cmd)
    a1s = alu_input1_structured(cmd)
    selrn = bf(cmd, 21, 19)
    selr = f"R{selrn}"
    if dins13(cmd):  # we
        dest = selr
        a0_is_dest = a0 == dest
        if a0s.always_zero():
            if a1s.always_zero():
                return f"CLR {dest}"
            assert not sub
            if not dins11(cmd):
                assert a1 == "R0"
                return f"SWAP {a1},{dest}"
            elif dins14(cmd):
                assert a1 == "R1"
                return f"SWAP {a1},{dest}"
            elif isinstance(a1s, OredRegisterInput) and a1s.n == selrn:
                return f"OR #{a1s.mask:x},{dest}"
            else:
                return f"MOV {a1s},{dest}"
        assert dins11(cmd) and not dins14(cmd)
        if a1s.always_zero():
            if isinstance(a0s, MaskedRegisterInput) and a0s.n == selrn:
                return f"AND #{a0s.mask:x},{dest}"
            if isinstance(a0s, LeftShiftedRegisterInput) and a0s.n == selrn:
                return f"SHL {dest}"
            if isinstance(a0s, PushDigitInput) and a0s.n == selrn:
                return f"INSH #{a0s.digit:x},{dest}"
            return f"MOV {a0s},{dest}"
        else:
            if (not sub and isinstance(a0s, LeftShiftedRegisterInput) and
                isinstance(a1s, ConstantInput) and a0s.n == selrn):
                return f"INSL #{a1s.n:x},{dest}"
            op = "SUB" if sub else "ADD"
            if a0_is_dest:
                return f"{op} {a1s},{dest}"
            else:
                return f"{op} {a0},{a1s},{dest}"
    else:  # not we
        if a0s.always_zero() and a1s.always_zero():
            if not dins11(cmd):
                return f"MOV {selr},R0"
            elif dins14(cmd):
                return f"MOV {selr},R1"
            else:
                return f"NOP{bf(cmd, 18, 14)}"
        assert dins11(cmd) and not dins14(cmd)
        if sub:
            if a1s.always_zero() and isinstance(a0s, MaskedRegisterInput):
                return f"TST #{a0s.mask:x},R{a0s.n}"
            return f"CMP {a1s},{a0s}"
        else:
            return f"CMPN {a1s},{a0s}"
    return "???"


def decode_instr(adr, cmd, skip_adr=False):
    i = decode_main_instr(adr, cmd)
    if dins10(cmd):
        wcode = bf(cmd, 13, 10)
        w = decode_window(wcode)
        if w[0] != w[1]:
            i += f" [{w[1]}:{w[0]}]"
        else:
            i += f" [{w[0]}]"
        if has_decimal_adjustment(wcode):
            i += ".D"
    if not skip_adr:
        if is_call(cmd):
            i += f" R:{instr_return_adr(cmd):03x}"
        elif not is_return(cmd) and not is_jump(cmd):
            na = imm_next_adr(adr, cmd)
            i += f" N:{na:03x}"
            if is_branch_c(cmd) and na & 0x10 == 0 and branch_c_possible(cmd):
                i += ",C"
            if is_branch_z(cmd) and na & 0x20 == 0:
                i += ",Z"
    return i


def print_microcode(mc):
    for i in range(16 * 64):
        cmd = mc.get(i)
        print(f"{i:03x} {cmd:022b} {next_adr(i, cmd):03x} {mcode_cmd_info(cmd)}")

def print_cmd_info(adr, cmd):
    di = decode_instr(adr, cmd)
    if not di: di = "???"
    print(f"{adr:03x}: {di:15s}")
    print(f"                     "
          f"alu0: {alu_input0(cmd):7s} alu1: {alu_input1(cmd):7s}")
    print(f"                     ins:{bf(cmd, 18, 14):05b} "
          f"reg/stc:{bf(cmd, 21, 19):01x} "
          f"w/str:{bf(cmd, 13, 10):01x} ac1:{bf(cmd, 2, 0):01x} "
          f"ac0:{bf(cmd, 5, 3):01x} ar/imm:{bf(cmd, 9, 6)} "
          f"we:{int(dins13(cmd))}")

def microcode_paths(mc):
    ret_cols = call_return_cols(mc)
    def refs_info(ind, r):
        if ind < 2:
            return ""
        return "(from " + ",".join([f"{a:03x}" for a in r]) + ")"

    def next_adrs(adr, cmd, ret_cols):
        return [ea for ea, el in outgoing_edges(adr, cmd, ret_cols)]

    n = 16 * 64
    indeg = np.zeros((n,), dtype=int)
    refs = {}
    for i in range(n):
        cmd = mc.get(i)
        for na in next_adrs(i, cmd, ret_cols):
            indeg[na] += 1
            refs.setdefault(na, []).append(i)

    done = np.zeros((n,), dtype=bool)
    while True:
        for i in range(n):
            if not done[i] and (i == 0 or indeg[i] == 0):
                break
        else:
            for i in range(n):
                if not done[i]: break
            else:
                break
        branches = []
        while True:
            done[i] = True
            cmd = mc.get(i)
            print_cmd_info(i, cmd)
            ri = refs_info(indeg[i], refs.get(i, []))
            if ri:
                print(" " * 21 + ri)
            for e in outgoing_edges(i, cmd, ret_cols):
                print(f"  {e[1]}: {e[0]:03x}")
                branches.append(e[0])
            while branches and done[branches[-1]]:
                branches.pop()
            if not branches: break
            i = branches.pop()
        print("=================")

def microcode_graph(mc):
    ret_cols = call_return_cols(mc)
    print("digraph {")
    for a in range(1024):
        cmd = mc.get(a)
        print(f'i{a:03x} [label="{a:03x} '
              f'{decode_instr(a, cmd, skip_adr=True)}"];')

        for e in outgoing_edges(a, cmd, ret_cols):
            print(f'i{a:03x} -> i{e[0]:03x} [label="{e[1]}"]')
    print("}")

def instruction_table(imm=3):
    for instr in range(32):
        cmd = (instr << 14) | (5 << 19) | (imm << 6)
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

def call_return_cols(mc):
    searching = set()
    ret_cols = {}

    def do_find_returns(a, level):
        stack = [a]
        visited = set()
        returns = set()
        while stack:
            a = stack.pop()
            if a in visited: continue
            visited.add(a)
            cmd = mc.get(a)
            if is_return(cmd):
                returns.add(
                    cons_adr(instr_next_colh(cmd), instr_next_coll(cmd), 0))
                continue
            if is_call(cmd):
                ca = imm_next_adr(a, cmd)
                if ca not in ret_cols:
                    print("  " * level + f"  recursive search for {ca:03x}")
                    find_returns(ca, level + 1)
                rcol = ret_cols.get(ca, None)
                if rcol is not None:
                    outg = outgoing_edges(a, cmd, ret_cols)
                else:
                    print(f"  {ca:03x} ???")
                    # TODO: there are many cases where we get here because
                    # of recursion cycles. Do these cycles actually happen?
                    # Does the code purposefully leave a return value
                    # on stack to do a non-local exit?
                    # return None
                    continue
            else:
                outg = outgoing_edges(a, cmd, ret_cols)
            for ea, el in outg:
                stack.append(ea)
        if not returns:
            print("no returns found")
            return None
        sl = sorted(list(returns))
        return [(a, f"R{i}") for i, a in enumerate(sl)]

    def find_returns(a, level=0):
        if a in ret_cols:
            return ret_cols[a]
        if a in searching:
            print("  " * level + f"recursion cycle with {a:03x}")
            return None
        searching.add(a)
        try:
            r = do_find_returns(a, level)
            if r is not None:
                rastr = ','.join([f'{ra:03x}' for ra, l in r])
                print("  " * level + f"call {a:03x} -> {rastr}")
            ret_cols[a] = r
        finally:
            searching.remove(a)
        return r

    for a in range(0x400):
        cmd = mc.get(a)
        if is_call(cmd):
            ca = imm_next_adr(a, cmd)
            if ca not in ret_cols:
                r = find_returns(ca)
                # TODO: remove the rest?
                continue
                if r:
                    ret_cols[ca] = r
                    rastr = ','.join([f'{ra:03x}' for ra, l in r])
                    print(f"{ca:03x} -> {rastr}")
                else:
                    print(f"{ca:03x} not found")

    n_valid = 0
    for a, r in ret_cols.items():
        if r is not None: n_valid += 1
    print(f"found returns: {n_valid}/{len(ret_cols)}")
    return ret_cols
