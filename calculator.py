from decimal import Decimal
import re

def get_display(e):
    num = ""
    ind = ""
    ind_txt = ["?0", "F", "?2", "M", "K", "DEG", "RAD", "GRA", "SD"]
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
