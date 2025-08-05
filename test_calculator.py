#!/usr/bin/python3

import math, unittest
from decimal import Decimal

import emulator
from calculator import *
from keys import *
from program import Program

class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.emulator = emulator.Emulator(Program.from_file())

    def press(self, keys):
        execute_seq(self.emulator, keys)

    def num(self):
        return get_display_num(self.emulator)

    def test_add(self):
        self.press([K1, K2, KPLUS, K3, K4, KEQ])
        self.assertEqual(self.num(), 12 + 34)
        self.press([K1, KP, K2, K3, K4, KPLUS, K5, K6, K7, KP, K8, KEQ])
        self.press([K1, KPLUS, K2, KNEG, KEQ])

    def test_mul(self):
        self.press([K1, K2, KMUL, K3, K4, KEQ])
        self.assertEqual(self.num(), 12 * 34)
        self.press([K1, KP, K2, K3, K4, KMUL, K5, K6, K7, KP, K8, KEQ])
        self.assertEqual(self.num(), Decimal("1.234") * Decimal("567.8"))

    def test_div(self):
        self.press([K7, K2, KDIV, K9, KEQ])

    def test_sin(self):
        self.press([K4, K5, KSIN])
        self.press([K3, K0, KSIN])
        self.press([K4, K0, K5, KSIN])

    def test_sin_rad(self):
        # TODO: KPI should require KF before it
        self.press([KMODE, KPI, KDIV, K6, KEQ, KSIN])

    def test_cos(self):
        self.press([K6, K0, KCOS])
        self.press([K3, K0, KCOS])

    def test_exp_form(self):
        self.press([K7, K8, KF, KPI, K1, K2, KPLUS, K1, KF, KPI, K1, K1, KEQ])
        self.assertEqual(self.num(), Decimal("78e12") + Decimal("1e11"))
        self.press([K7, K8, KF, KPI, K1, K2, KNEG, KPLUS,
               K1, KF, KPI, K1, K1, KNEG, KEQ])
        self.assertEqual(self.num(), Decimal("78e-12") + Decimal("1e-11"))

    def test_sqrt(self):
        self.press([K1, K2, K3, KSQRT])
        # TODO: replace with a function that compares significant digits
        self.assertAlmostEqual(float(self.num()), math.sqrt(123), places=4)

if __name__ == "__main__":
    unittest.main()
