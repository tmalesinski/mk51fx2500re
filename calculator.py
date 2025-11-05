from decimal import Decimal
import re

def get_display(e, fx2500=True):
    num = ""
    ind = ""
    if fx2500:
        ind_txt = ["F1", "F", "INV", "M", "K", "DEG", "RAD", "GRA", "SD"]
    else:
        ind_txt = ["F1", "F2", "INV", "M", "K", "DEG", "RAD", "GRA", "SD"]
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
        ind += ind_txt[i] if p & 4 else " " * len(ind_txt[i])
        ind += " "
    return num, ind


def get_display_num(e):
    num, _ = get_display(e)
    m = re.match(r" *(-?\d+(?:.\d*)?)$", num)
    if m: return Decimal(m.group(1))
    m = re.match(r" *(-?\d+(?:.\d*)?)([ -]\d\d)$", num)
    if m: return Decimal(m.group(1) + "e" + m.group(2).strip())
    raise ValueError(num)

def execute_seq(e, keys, print_disp=True):
    for k in keys:
        e.keycode = 0
        e.until(0x3c5)
        e.keycode = k
        e.until(0x3c3)
        if print_disp:
            num, ind = get_display(e)
            print(f"{num}|{ind}")

def decode_num(r):
    d = [r[i] for i in range(12, 1, -1)]
    e = r[1] * 10 + r[0]
    if r[13] & 2: e = -e
    return Decimal((r[13] >> 3, d, e - 10))

def set_num(emul, r, x):
    reg = emul.regs[r]
    _, digits, exp = Decimal(x).as_tuple()
    exp += len(digits) - 1
    if abs(exp) > 99: raise ValueError("exponent too large")
    reg[13] = (int(x < 0) << 3) | (int(exp < 0) << 1)
    reg[12:1:-1] = list(digits[:11]) + [0] * max(0, 11 - len(digits))
    reg[0] = abs(exp) % 10
    reg[1] = abs(exp) // 10
