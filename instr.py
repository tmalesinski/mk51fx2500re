from bits import bf, bit
import windows

__all__ = [
    "make_adr",
    "instr_next_colh", "instr_next_coll", "instr_has_next_row",
    "instr_next_adr", "instr_return_adr",
    "instr_op",
    "is_jump", "is_call", "is_return", "is_const",
    "is_branch_z", "is_branch_c",
    "instr_masked_reg", "instr_shl", "instr_insel0", "instr_field_en",
    "instr_selr_to_r0", "instr_selr_to_r1", "instr_alu_sub", "instr_we",
    "RegisterInput", "KeyCodeInput", "ConstantInput", "Kr0Input",
    "MaskedRegisterInput", "OredRegisterInput", "PushDigitInput",
    "LeftShiftedRegisterInput",
    "alu_input0", "alu_input1"
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

def is_branch_z(instr):
    return bf(instr, 16, 15) == 3 and ((bf(instr, 18, 14) & 0x19) != 0)

def is_branch_c(instr):
    return bit(instr, 15) and not is_return(instr)

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


def alu_input0(instr):
    imm = bf(instr, 9, 6)
    selr = bf(instr, 21, 19)
    res = []
    if bf(instr, 18, 17) != 0 and instr_insel0(instr):
        res.append(RegisterInput(selr))
    if instr_masked_reg(instr) and bf(instr, 9, 6) == 0:
        res.append(Kr0Input())
    if instr_masked_reg(instr) and bf(instr, 9, 6) != 0:
        res.append(MaskedRegisterInput(selr, imm))
    if is_const(instr):
        res.append(PushDigitInput(selr, imm))
    if instr_shl(instr):
        w = windows.decode_window(bf(instr, 13, 10))
        if w[0] == w[1]:
            res.append(ConstantInput(0))
        else:
            res.append(LeftShiftedRegisterInput(selr))
    if not res:
        res.append(ConstantInput(0))
    assert len(res) == 1
    return res[0]

def alu_input1(instr):
    res = []
    if bit(instr, 18):
        res.append(RegisterInput(1 if bit(instr, 17) else 0))
    if not bit(instr, 18) and bit(instr, 17):
        if bf(instr, 9, 6) == 0 and instr_insel0(instr):
            res.append(KeyCodeInput())
        if bf(instr, 9, 6) != 0:
            res.append(ConstantInput(bf(instr, 9, 6)))
    if instr_shl(instr):
        if not bit(instr, 13) and (not bit(instr, 12) or bit(instr, 11)):
            # TODO: does it only happen with one element fields and
            # is it then or with an immediate?
            res.append(RegisterInput(bf(instr, 21, 19)))
    if not res:
        res.append(ConstantInput(0))
    if len(res) == 2:
        if (isinstance(res[0], ConstantInput) and
            isinstance(res[1], RegisterInput)):
            res = [OredRegisterInput(res[1].n, res[0].n)]
    assert len(res) == 1, res
    return res[0]
