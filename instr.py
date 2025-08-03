from bits import bf, bit

__all__ = [
    "make_adr",
    "instr_next_colh", "instr_next_coll", "instr_has_next_row",
    "instr_next_adr", "instr_return_adr",
    "instr_op",
    "is_jump", "is_call", "is_return", "is_const",
    "instr_masked_reg", "instr_shl", "instr_insel0", "instr_field_en",
    "instr_selr_to_r0", "instr_selr_to_r1", "instr_alu_sub", "instr_we"
]

# TODO: consider changing the convention to row, colh, coll.
# Row address generally stays the same in related pieces of code.
def make_adr(colh, coll, row):
    return (colh << 7) | (coll << 4) | row

def instr_next_colh(instr):
    return bf(instr, 2, 0)

def instr_next_coll(instr):
    return bf(instr, 5, 3)

def instr_has_next_row(cmd):
    return (bf(cmd, 18, 17) != 1 and bf(cmd, 18, 14) != 2 and
            bf(cmd, 18, 15) != 3)

def instr_next_adr(adr, cmd):
    n = ((cmd & 7) << 7) | (((cmd >> 3) & 7) << 4)
    if instr_has_next_row(cmd):
        n |= (cmd >> 6) & 0xf
    else:
        n |= adr & 0xf
    return n

def instr_return_adr(instr):
    return make_adr(0, bf(instr, 21, 19), bf(instr, 13, 10))

def instr_op(instr):
    return (instr >> 14) & 0x1f

def is_jump(instr):
    return instr_op(instr) == 0

def is_call(instr):
    return instr_op(instr) == 1

def is_return(instr):
    return instr_op(instr) == 3

# TODO: rename to is_insl?
def is_const(instr):
    return instr_op(instr) == 2

# ALU input 0: masked selected shift reg or KR0
def instr_masked_reg(cmd):
    return bf(cmd, 18, 15) == 3

# ALU input 0: selected shift reg but only on some windows
# ALU input 1: delayed selected reg when in window
def instr_shl(cmd):
    return bf(cmd, 18, 14) == 0xd

# Partial signal used in ALU input selection.
# ALU input 0: selected shift reg (with particular MCD 17 and MCD 18)
# ALU input 1: KEY (wih particular MCD17 and MCD 18)
def instr_insel0(cmd):
    return bf(cmd, 15, 14) != 1

# Enable field (otherwise finish instruction on the next digit)
def instr_field_en(instr):
    return not (bf(instr, 18, 16) == 0 and bf(instr, 15, 14) != 2)

# Move the selected register to R0.
def instr_selr_to_r0(cmd):
    return bf(cmd, 17, 14) == 5

# Move the selected register to R1.
def instr_selr_to_r1(instr):
    return bf(instr, 18, 14) == 0x1d or bf(instr, 18, 14) == 4

# Add/sub.
def instr_alu_sub(instr):
    return not (bf(instr, 15, 14) == 1 or not bit(instr, 16))

# Write enable for shift registers
def instr_we(instr):
    int1 = bf(instr, 18, 17) == 0 or bit(instr, 15)
    int2 = bf(instr, 15, 14) != 2
    return not (int1 and int2)
