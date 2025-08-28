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

    def test_forensics(self):
        # From https://www.rskey.org/~mwsebastian/miscprj/models.htm
        self.press([K9, KSIN, KCOS, KTAN, KF, KTAN, KF, KCOS, KF, KSIN])
        self.assertEqual(self.num(), Decimal("8.9911614"))

    def test_decode_positive_number(self):
        self.press([K1, K2, K3])
        self.emulator.call(0x200)
        self.assertEqual(decode_num(self.emulator.regs[0]), 123)

    def test_decode_fractional_number(self):
        self.press([K1, K2, K3, KP, K4, K5])
        self.emulator.call(0x200)
        self.assertEqual(decode_num(self.emulator.regs[0]), Decimal("123.45"))

    def test_decode_zero(self):
        self.emulator.call(0x200)
        self.assertEqual(decode_num(self.emulator.regs[0]), 0)

    def test_decode_negative_number(self):
        self.press([K1, K2, KNEG])
        self.emulator.call(0x200)
        self.assertEqual(decode_num(self.emulator.regs[0]), -12)

    def test_decode_large_exponent(self):
        self.press([K1, K2, KPI, K3, K4])
        self.emulator.call(0x200)
        self.assertEqual(decode_num(self.emulator.regs[0]), Decimal("12e34"))

    def test_decode_low_fractional_number(self):
        self.press([KP, K0, K0, K0, K1, K2])
        self.emulator.call(0x200)
        self.emulator.print_state()
        self.assertEqual(decode_num(self.emulator.regs[0]), Decimal("0.00012"))

    def test_decode_negative_large_negative_exponent(self):
        self.press([K1, K2, KP, K3, KNEG, KPI, K4, K5, KNEG])
        self.emulator.call(0x200)
        self.assertEqual(decode_num(self.emulator.regs[0]),
                         Decimal("-12.3e-45"))

    def test_set_num(self):
        for x in [Decimal("1234.56"), Decimal("-1234.56"),
                  Decimal("0.000001234"), 1, 0]:
            set_num(self.emulator, 0, x)
            self.assertEqual(decode_num(self.emulator.regs[0]), x)


if __name__ == "__main__":
    unittest.main()
