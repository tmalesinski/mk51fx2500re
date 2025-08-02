from emulator import Emulator
from analyze import Microcode, load_microcode_from_txt


K1 = (0, 4)
K2 = (1, 4)
K3 = (2, 4)
K4 = (0, 2)
K5 = (1, 2)
K6 = (2, 2)
K7 = (3, 2)
K8 = (4, 2)
K9 = (5, 2)
K0 = (3, 4)
KC = (0, 8)
KPLUS = (5, 8)
KEQ = (5, 4)
KMINUS = (4, 8)
KSQRT = (1, 1)
KMUL = (3, 8)
KSIN = (3, 12)
KLOG = (0, 12)
KLN = (1, 12)
KPOW = (2, 12)
KPI = (6, 4)
KF = (5, 1)
KMODE = (7, 1)
KMIN = (6, 8)
KMR = (7, 8)
KP = (4, 4)
KINV = (6, 2)
KDMS = (6, 12)

def create_emulator():
    return Emulator(Microcode(load_microcode_from_txt()))

def call(e, adr):
    e.pc = adr
    e.cont(until_return=True)

def reg_str(r):
    return "".join(f"{d:x}" for d in reversed(r))

def test_pi():
    e = create_emulator()
    call(e, 0x143)
    return reg_str(e.regs[0])

def test_pi180():
    e = create_emulator()
    call(e, 0x379)
    return reg_str(e.regs[1])

def test_ln10():
    e = create_emulator()
    call(e, 0x2c9)
    return reg_str(e.regs[1])

def test_ln_cordic():
    res = []
    for i in range(15):
        e = create_emulator()
        e.regs[0][0] = i
        call(e, 0x280)
        res.append(reg_str(e.regs[1]))
    return res

# TODO: check correctness, in particular the dest register at 030 should
# probably be R1 (incorrect bit in the ROM read).
def test_tan_cordic():
    res = []
    for i in range(15):
        e = create_emulator()
        e.regs[0][0] = i
        call(e, 0x010)
        res.append(reg_str(e.regs[1]))
    return res

def get_key_trace(row, col_code):
    e = create_emulator()
    e.add_break(0x3f)
    e.cont()
    e.del_all_breaks()
    e.add_break(0x5f)
    e.cont(50)
    e.del_all_breaks()
    e.keycode = (row, col_code)
    trace = []
    for i in range(100):
        e.step()
        trace.append(e.pc)
    return trace

def get_key_traces():
    traces = []
    for row in range(8):
        for col_code in range(1, 15):
            if col_code >= 4 and col_code & 3 != 0: continue
            trace = get_key_trace(row, col_code)
            traces.append((row, col_code, trace))
    traces.sort(key=lambda t: t[2])
    for row, col_code, trace in traces:
        trstr = " ".join(f"{a:03x}" for a in trace)
        print(f"{row} {col_code:x}: {trstr}")

def display(e):
    num = ""
    ind = ""
    for i in range(8):
        d = e.regs[0][11 - i]
        if d <= 9:
            num += str(d)
        elif d == 13:
            num += "E"
        elif d == 14:
            num += "-"
        else:
            num += " "
        p = e.regs[1][11 - i]
        if p & 8:
            num += "."
        ind += str(i) if p & 4 else "_"
    return f"|{num}| {ind}"

def get_disp_after_keys():
    for row in range(8):
        for col_code in range(1, 15):
            if col_code >= 4 and col_code & 3 != 0: continue
            e = create_emulator()
            e.add_break(0x5f)
            e.cont()
            e.del_all_breaks()
            e.keycode = (row, col_code)
            e.add_break(0x3f)
            e.cont()
            print(row, f"{col_code:x}", display(e))

def execute_seq(keys, trace=False):
    e = create_emulator()
    for k in keys:
        e.keycode = (0, 0)
        e.add_break(0x5f)
        e.cont()
        e.del_all_breaks()
        e.keycode = k
        e.add_break(0x3f)
        e.cont(trace=trace)
        e.del_all_breaks()
        print(display(e))
