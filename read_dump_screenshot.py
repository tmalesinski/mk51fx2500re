#!/usr/bin/python3

import imageio
import numpy as np

# 16, 50 - 3233, 1456

# some x positions of leftmost 1 pixel
# 17, 118, 163, 291, 675, 1096, 2650, 3225
xpos = np.array([
    (0, 17),
    (1, 26),
    (2, 35),
    (3, 44),
    (5, 63),
    (8, 90),
    (12, 118),
])

CHW = 9.14
CHH = 22

def decode(img):
    res = []

    for i in range(64):
        line = []
        for j in range(22 * 16):
            x0 = int(16 + CHW * j)
            y0 = 50 + CHH * i
            n = np.sum(img[y0:y0 + CHH, x0:x0 + int(CHW), 0])
            line.append(n > 44250)
        res.append(line)
    return np.array(res).astype(int)

def dump_str(bits):
    rows = []
    rows = ["".join(str(b) for b in row) + "\n" for row in bits]
    return "".join(rows)

def main():
    bits = decode(imageio.imread("img/mk51_rom_dump_screen.png"))
    print(dump_str(bits), end="")

if __name__ == "__main__":
    main()
