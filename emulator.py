import analyze
from analyze import is_call, is_return, instr_return_adr, imm_next_adr
from analyze import is_sub, dins11, dins13, dins14, is_branch_z, is_branch_c
from analyze import alu_input0_structured, alu_input1_structured
from analyze import bf
from analyze import decode_instr
from analyze import Microcode, load_microcode_from_txt
from windows import decode_window, has_decimal_adjustment

def instr_field(instr):
    return bf(instr, 13, 10)

def instr_reg(instr):
    return bf(instr, 21, 19)

_STACK_SIZE = 5

class Emulator:
    def __init__(self, microcode):
        self.mc = microcode
        self.pc = 0

        self.regs = []
        for i in range(8):
            self.regs.append([0] * 15)

        self.stack = [0] * _STACK_SIZE
        self.sp = 0

        self.keycode = (0, 0)

    def _get_input(self, inp, field):
        fs = slice(field[0], field[1] + 1)
        if isinstance(inp, analyze.RegisterInput):
            return self.regs[inp.n][fs]
        if isinstance(inp, analyze.KeyCodeInput):
            r = [0] * 15
            r[13 - self.keycode[0]] = self.keycode[1]
            return r[fs]
        if isinstance(inp, analyze.ConstantInput):
            r = [0] * (field[1] - field[0] + 1)
            r[0] = inp.n
            return r
        # TODO: Kr0Input?
        if isinstance(inp, analyze.MaskedRegisterInput):
            return [d & inp.mask for d in self.regs[inp.n][fs]]
        if isinstance(inp, analyze.OredRegisterInput):
            return [d | inp.mask for d in self.regs[inp.n][fs]]
        if isinstance(inp, analyze.PushDigitInput):
            r = self.regs[inp.n][fs]
            return r[1:] + [inp.digit]
        if isinstance(inp, analyze.LeftShiftedRegisterInput):
            r = self.regs[inp.n][fs]
            return [0] + r[:-1]
        raise NotImplementedError(inp)

    def _execute_alu_instr(self, instr):
        fcode = instr_field(instr)
        field = decode_window(fcode)

        a0 = alu_input0_structured(instr)
        a1 = alu_input1_structured(instr)

        v0 = self._get_input(a0, field)
        v1 = self._get_input(a1, field)
        assert len(v0) == len(v1)
        assert len(v0) == field[1] - field[0] + 1

        # TODO: disable decimal adjustment on one digit for fcode == 0xc
        base = 10 if has_decimal_adjustment(fcode) else 16
        c = 0
        res = []
        for a, b in zip(v0, v1):
            if not is_sub(instr):
                r = a + b + c
                c = int(r >= base)
            else:
                r = a - b - c
                c = int(r < 0)
            res.append(r % base)

        fs = slice(field[0], field[1] + 1)
        selr = instr_reg(instr)
        if dins13(instr):  # we
            self.regs[selr][fs] = res
        if not dins11(instr):
            self.regs[0][fs] = self.regs[selr][fs]
        if dins14(instr):
            self.regs[1][fs] = self.regs[selr][fs]

        self.pc = imm_next_adr(self.pc, instr)
        if is_branch_c(instr) and c:
            self.pc |= 0x10
        if is_branch_z(instr) and not all([d == 0 for d in res]):
            self.pc |= 0x20

    def step(self):
        instr = self.mc.get(self.pc)
        next_adr = imm_next_adr(self.pc, instr)

        if is_call(instr):
            self.stack[self.sp] = instr_return_adr(instr)
            self.sp = (self.sp + 1) % _STACK_SIZE
            self.pc = next_adr
        elif is_return(instr):
            self.sp = (self.sp - 1) % _STACK_SIZE
            self.pc = self.stack[self.sp] | next_adr
            return
        else:
            self._execute_alu_instr(instr)

    def print_state(self):
        for i in range(2):
            for j in range(4):
                n = i * 4 + j
                r = self.regs[n]
                rs = "".join(f"{d:x}" for d in reversed(self.regs[n]))
                print(f"R{n}={rs} ", end="")
            print()
        st = [self.stack[(self.sp - i - 1) % _STACK_SIZE] for i in range(5)]
        print(f"S: {' '.join(f'{a:03x}' for a in st)}")
        print(f"{self.pc:03x} {decode_instr(self.pc, self.mc.get(self.pc))}")

