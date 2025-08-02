#!/usr/bin/python3

import unittest

import emulator
from analyze import Microcode, load_microcode_from_txt

# TODO: move it to emulator?
K1 = (0, 4)
K2 = (1, 4)
K3 = (2, 4)
K4 = (0, 2)
KPLUS = (5, 8)
KEQ = (5, 4)

class TestEmulator(unittest.TestCase):
    def setUp(self):
        self.emulator = emulator.Emulator(Microcode(load_microcode_from_txt()))

    def _execute_seq(self, keys):
        for k in keys:
            self.emulator.keycode = (0, 0)
            self.emulator.add_break(0x5f)
            self.emulator.cont()
            self.emulator.del_all_breaks()
            self.emulator.keycode = k
            self.emulator.add_break(0x3f)
            self.emulator.cont()
            self.emulator.del_all_breaks()
        return "".join(f"{d:x}" for d in self.emulator.regs[0][12:3:-1])

    def test_add(self):
        d = self._execute_seq([K1, K2, KPLUS, K3, K4, KEQ])
        self.assertEqual(d, "fffffff46")

if __name__ == "__main__":
    unittest.main()
