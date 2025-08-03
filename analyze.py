#!/usr/bin/python

import numpy as np

from bits import *
from instr import *
from program import *
from field import decode_field, has_decimal_adjustment

def return_adrs(adr, cmd, ret_cols=None):
    # TODO: fail on missing returns instead of this guess?
    rcols = [(make_adr(0, instr_next_colh(cmd), 0), "")]
    if ret_cols is not None:
        rs = ret_cols.get(instr_next_adr(adr, cmd), None)
        if rs is not None:
            rcols = rs
    padr = instr_return_adr(cmd)
    return [(r | padr, l) for r, l in rcols]

def branch_c_possible(cmd):
    a0 = alu_input0(cmd)
    a1 = alu_input1(cmd)
    # TODO: seems wrong on sub with a0 == 0 (if it happens at all)
    return not a0.always_zero() and not a1.always_zero()

def cz_possible(cmd, c, z):
    if c is None:
        return cz_possible(cmd, True, z) or cz_possible(cmd, False, z)
    if z is None:
        return cz_possible(cmd, c, True) or cz_possible(cmd, c, False)
    if c and alu_input1(cmd).always_zero():
        return False
    if c and z and instr_alu_sub(cmd):
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
    na = instr_next_adr(adr, cmd)
    c_enabled = is_branch_c(cmd) and na & 1 == 0
    z_enabled = is_branch_z(cmd) and na & 2 == 0
    edges = []
    for c in [True, False] if c_enabled else [None]:
        for z in [True, False] if z_enabled else [None]:
            if not cz_possible(cmd, c, z):
                continue
            a = na
            if is_branch_c(cmd) and c:
                a |= 1
            if is_branch_z(cmd) and not z:
                a |= 2
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
        return f"JUMP {instr_next_adr(adr, cmd):03x}"
    if is_call(cmd):
        return f"CALL {instr_next_adr(adr, cmd):03x}"
    if is_return(cmd):
        return f"RETURN {instr_next_adr(adr, cmd):03x}"
    sub = instr_alu_sub(cmd)
    a0s = alu_input0(cmd)
    # TODO: stop using a0 and a1, rename a0s, a1s to a0, a1
    a0 = str(a0s)
    a1s = alu_input1(cmd)
    a1 = str(a1s)
    selrn = bf(cmd, 21, 19)
    selr = f"R{selrn}"
    if instr_we(cmd):
        dest = selr
        a0_is_dest = a0 == dest
        if a0s.always_zero():
            if a1s.always_zero():
                return f"CLR {dest}"
            assert not sub
            if instr_selr_to_r0(cmd):
                assert a1 == "R0"
                return f"SWAP {a1},{dest}"
            elif instr_selr_to_r1(cmd):
                assert a1 == "R1"
                return f"SWAP {a1},{dest}"
            elif isinstance(a1s, OredRegisterInput) and a1s.n == selrn:
                return f"OR #{a1s.mask:x},{dest}"
            else:
                return f"MOV {a1s},{dest}"
        assert not instr_selr_to_r0(cmd) and not instr_selr_to_r1(cmd)
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
            if instr_selr_to_r0(cmd):
                return f"MOV {selr},R0"
            elif instr_selr_to_r1(cmd):
                return f"MOV {selr},R1"
            else:
                return f"NOP{bf(cmd, 18, 14)}"
        assert not instr_selr_to_r0(cmd) and not instr_selr_to_r1(cmd)
        if sub:
            if a1s.always_zero() and isinstance(a0s, MaskedRegisterInput):
                return f"TST #{a0s.mask:x},R{a0s.n}"
            return f"CMP {a1s},{a0s}"
        else:
            return f"CMPN {a1s},{a0s}"
    return "???"


def decode_instr(adr, cmd, skip_adr=False):
    i = decode_main_instr(adr, cmd)
    if instr_field_en(cmd):
        fcode = bf(cmd, 13, 10)
        f = decode_field(fcode)
        if f[0] != f[1]:
            i += f" [{f[1]}:{f[0]}]"
        else:
            i += f" [{f[0]}]"
        if has_decimal_adjustment(fcode):
            i += ".D"
    if not skip_adr:
        if is_call(cmd):
            i += f" R:{instr_return_adr(cmd):03x}"
        elif not is_return(cmd) and not is_jump(cmd):
            na = instr_next_adr(adr, cmd)
            i += f" N:{na:03x}"
            if is_branch_c(cmd) and na & 0x10 == 0 and branch_c_possible(cmd):
                i += ",C"
            if is_branch_z(cmd) and na & 0x20 == 0:
                i += ",Z"
    return i


def print_cmd_info(adr, cmd):
    di = decode_instr(adr, cmd)
    if not di: di = "???"
    print(f"{adr:03x}: {di:15s}")
    print(f"                     "
          f"alu0: {alu_input0(cmd)!s:7s} alu1: {alu_input1(cmd)!s:7s}")
    print(f"                     ins:{bf(cmd, 18, 14):05b} "
          f"reg/stc:{bf(cmd, 21, 19):01x} "
          f"w/str:{bf(cmd, 13, 10):01x} ac1:{bf(cmd, 2, 0):01x} "
          f"ac0:{bf(cmd, 5, 3):01x} ar/imm:{bf(cmd, 9, 6)} "
          f"we:{int(instr_we(cmd))}")

def program_paths(prog):
    ret_cols = call_return_cols(prog)
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
        cmd = prog.get(i)
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
            cmd = prog.get(i)
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

def program_graph(prog):
    ret_cols = call_return_cols(prog)
    print("digraph {")
    for a in range(1024):
        cmd = prog.get(a)
        print(f'i{a:03x} [label="{a:03x} '
              f'{decode_instr(a, cmd, skip_adr=True)}"];')

        for e in outgoing_edges(a, cmd, ret_cols):
            print(f'i{a:03x} -> i{e[0]:03x} [label="{e[1]}"]')
    print("}")

def instruction_table(imm=3):
    for instr in range(32):
        cmd = (instr << 14) | (5 << 19) | (imm << 6)
        print(f"{instr:05b} "
              f"{alu_input0(cmd)!s:10s} "
              f"{alu_input1(cmd)!s:10s} "
              f"rowadr:{int(instr_has_next_row(cmd))} "
              f"we: {int(instr_we(cmd))} "
              f"sub: {int(instr_alu_sub(cmd))} "
              f"brz: {int(is_branch_z(cmd))} "
              f"brc: {int(is_branch_c(cmd))} "
              f"call: {int(is_call(cmd))} "
              f"ret: {int(is_return(cmd))} "
              f"tor0: {int(instr_selr_to_r0(cmd))} "
              f"tor1: {int(instr_selr_to_r1(cmd))} "
              f"msk: {int(instr_masked_reg(cmd))} "
              f"cns: {int(is_const(cmd))} "
              f"shl: {int(instr_shl(cmd))} "
              f"is0: {int(instr_insel0(cmd))} "
              f"fen: {int(instr_field_en(cmd))}")

        print(decode_instr(0, cmd))

def call_return_cols(prog):
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
            cmd = prog.get(a)
            if is_return(cmd):
                returns.add(
                    make_adr(0, instr_next_colh(cmd), instr_next_coll(cmd)))
                continue
            if is_call(cmd):
                ca = instr_next_adr(a, cmd)
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
        cmd = prog.get(a)
        if is_call(cmd):
            ca = instr_next_adr(a, cmd)
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
