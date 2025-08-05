#!/usr/bin/python3

import unittest

import emulator
from keys import *
from program import Program


class TestEmulator(unittest.TestCase):
    def setUp(self):
        self.emulator = emulator.Emulator(Program.from_file())

    def _execute_seq(self, keys):
        for k in keys:
            self.emulator.keycode = 0
            self.emulator.add_break(0x3c5)
            self.emulator.cont()
            self.emulator.del_all_breaks()
            self.emulator.keycode = k
            self.emulator.add_break(0x3c3)
            self.emulator.cont()
            self.emulator.del_all_breaks()
        return "".join(f"{d:x}" for d in self.emulator.regs[0][12:3:-1])

    def test_add(self):
        d = self._execute_seq([K1, K2, KPLUS, K3, K4, KEQ])
        self.assertEqual(d, "fffffff46")

if __name__ == "__main__":
    unittest.main()
