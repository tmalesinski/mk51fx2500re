from bits import bf, bit

__all__ = [
    "make_adr",
    "instr_next_colh", "instr_next_coll", "instr_return_adr", "instr_op",
    "is_jump", "is_call", "is_return", "is_const",
]

# TODO: consider changing the convention to row, colh, coll.
# Row address generally stays the same in related pieces of code.
def make_adr(colh, coll, row):
    return (colh << 7) | (coll << 4) | row

def instr_next_colh(instr):
    return bf(instr, 2, 0)

def instr_next_coll(instr):
    return bf(instr, 5, 3)

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

def is_const(instr):
    return instr_op(instr) == 2

