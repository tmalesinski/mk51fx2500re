from bits import *
from instr import *
import analyze
from analyze import instr_next_adr, instr_alu_sub
from analyze import instr_selr_to_r0, instr_selr_to_r1, instr_we
from analyze import decode_instr
from program import *
from field import decode_field, has_decimal_adjustment
from field import partial_decimal_adjustment

def instr_field(instr):
    return bf(instr, 13, 10)

def instr_reg(instr):
    return bf(instr, 21, 19)

_STACK_SIZE = 5

class Emulator:
    def __init__(self, program):
        self.prog = program
        self.pc = 0

        self.regs = []
        for i in range(8):
            self.regs.append([0] * 15)

        self.stack = [0] * _STACK_SIZE
        self.sp = 0

        self.keycode = 0

        self.breaks = set()
        self.call_sp = None

    def _get_input(self, inp, field):
        fs = slice(field[0], field[1] + 1)
        if isinstance(inp, RegisterInput):
            return self.regs[inp.n][fs]
        if isinstance(inp, KeyCodeInput):
            r = [0] * 15
            r[13 - self.keycode // 10] = (
                [0, 1, 2, 4, 8, 12][self.keycode % 10])
            return r[fs]
        if isinstance(inp, ConstantInput):
            r = [0] * (field[1] - field[0] + 1)
            r[0] = inp.n
            return r
        # TODO: Kr0Input?
        if isinstance(inp, MaskedRegisterInput):
            return [d & inp.mask for d in self.regs[inp.n][fs]]
        if isinstance(inp, OredRegisterInput):
            return [d | inp.mask for d in self.regs[inp.n][fs]]
        if isinstance(inp, PushDigitInput):
            r = self.regs[inp.n][fs]
            return r[1:] + [inp.digit]
        if isinstance(inp, LeftShiftedRegisterInput):
            r = self.regs[inp.n][fs]
            return [0] + r[:-1]
        raise NotImplementedError(inp)

    def _execute_alu_instr(self, instr):
        fcode = instr_field(instr)
        field = decode_field(fcode)

        a0 = alu_input0(instr)
        a1 = alu_input1(instr)

        v0 = self._get_input(a0, field)
        v1 = self._get_input(a1, field)
        assert len(v0) == len(v1)
        assert len(v0) == field[1] - field[0] + 1

        base = 10 if has_decimal_adjustment(fcode) else 16
        partial_dec = partial_decimal_adjustment(fcode)
        c = 0
        res = []
        for i, (a, b) in enumerate(zip(v0, v1)):
            if partial_dec and i == 1:
                base = 16
            if not instr_alu_sub(instr):
                r = a + b + c
                c = int(r >= base)
            else:
                r = a - b - c
                c = int(r < 0)
            res.append(r % base)

        fs = slice(field[0], field[1] + 1)
        selr = instr_reg(instr)
        if instr_selr_to_r0(instr):
            self.regs[0][fs] = self.regs[selr][fs]
        if instr_selr_to_r1(instr):
            self.regs[1][fs] = self.regs[selr][fs]
        if instr_we(instr):
            self.regs[selr][fs] = res

        self.pc = instr_next_adr(self.pc, instr)
        if is_branch_c(instr) and c:
            self.pc |= 1
        if is_branch_z(instr) and not all([d == 0 for d in res]):
            self.pc |= 2

    def step(self):
        instr = self.prog.get(self.pc)
        next_adr = instr_next_adr(self.pc, instr)

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

    def cont(self, steps=None, trace=False):
        first = True
        while True:
            if steps is not None and steps == 0: return

            if not first and self.pc in self.breaks:
                return
            first = False
            if self.call_sp is not None:
                if (is_return(self.prog.get(self.pc)) and
                    self.call_sp == self.sp):
                    self.call_sp = None
                    return

            if steps is not None: steps -= 1
            self.step()
            if trace: self.print_state()

    def start_call(self, adr):
        self.call_sp = self.sp
        self.pc = adr

    def call(self, adr):
        self.start_call(adr)
        self.cont()

    def add_break(self, adr):
        self.breaks.add(adr)

    def del_break(self, adr):
        self.breaks.remove(adr)

    def del_all_breaks(self):
        self.breaks = set()

    def until(self, adr):
        # TODO: make until an option in cont, do not delete a breakpoint
        # if it already was one.
        self.breaks.add(adr)
        self.cont()
        self.del_break(adr)

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
        print(f"{self.pc:03x} {decode_instr(self.pc, self.prog.get(self.pc))}")

