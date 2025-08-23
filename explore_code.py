from emulator import Emulator
from keys import *
from program import Program
from analyze import decode_instr

def create_emulator():
    return Emulator(Program.from_file())

def call(e, adr):
    e.pc = adr
    e.cont(until_return=True)

def reg_str(r):
    return "".join(f"{d:x}" for d in reversed(r))

def test_pi():
    e = create_emulator()
    call(e, 0x0d4)
    return reg_str(e.regs[0])

def test_pi180():
    e = create_emulator()
    call(e, 0x277)
    return reg_str(e.regs[1])

def test_ln10():
    e = create_emulator()
    call(e, 0x26c)
    return reg_str(e.regs[1])

def test_ln_cordic():
    res = []
    for i in range(15):
        e = create_emulator()
        e.regs[0][0] = i
        call(e, 0x028)
        res.append(reg_str(e.regs[1]))
    return res

# TODO: check correctness, in particular the dest register at 030 should
# probably be R1 (incorrect bit in the ROM read).
def test_tan_cordic():
    res = []
    for i in range(15):
        e = create_emulator()
        e.regs[0][0] = i
        call(e, 0x1)
        res.append(reg_str(e.regs[1]))
    return res

def get_key_trace(key):
    e = create_emulator()
    e.keycode = 0
    e.until(0x3c5)
    e.keycode = key
    trace = []
    for i in range(200):
        e.step()
        trace.append(e.pc)
    return trace

def find_entry(key_trace, program):
    key_acc = False
    entry = key_trace[0]
    for a in key_trace:
        if a in [0x3ad, 0x380]: break
        if key_acc:
            entry = a
        instr = decode_instr(a, program.get(a))
        key_acc = False
        for p in ["R2 [14]", "R2 [13]", "R3 [14]"]:
            if p in instr:
                key_acc = True
                break
    return entry

def get_key_entries():
    traces = []
    emul = create_emulator()
    for row in range(8):
        for col in range(1, 6):
            key = row * 10 + col
            trace = get_key_trace(key)
            e = find_entry(trace, emul.prog)
            print(f"{key}: {e:03x}")

def display(e):
    num = ""
    ind = ""
    for i in range(9):
        d = e.regs[0][12 - i]
        if d <= 9:
            num += str(d)
        elif d == 13:
            num += "E"
        elif d == 14:
            num += "-"
        else:
            num += " "
        p = e.regs[1][12 - i]
        if p & 8:
            num += "."
        ind += str(i) if p & 4 else "_"
    return f"|{num}| {ind}"

def get_disp_after_keys():
    for row in range(8):
        for col_code in range(1, 15):
            if col_code >= 4 and col_code & 3 != 0: continue
            e = create_emulator()
            e.add_break(0x3c5)
            e.cont()
            e.del_all_breaks()
            e.keycode = (row, col_code)
            e.add_break(0x3c3)
            e.cont()
            print(row, f"{col_code:x}", display(e))

def execute_seq(keys, trace=False):
    e = create_emulator()
    for k in keys:
        e.keycode = 0
        e.add_break(0x3c5)
        e.cont()
        e.del_all_breaks()
        e.keycode = k
        e.add_break(0x3c3)
        e.cont(trace=trace)
        e.del_all_breaks()
        print(display(e))
