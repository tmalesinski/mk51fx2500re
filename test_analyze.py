#!/usr/bin/python3

import contextlib, io, unittest
from contextlib import redirect_stdout
from io import StringIO

import analyze

class TestAnalyze(unittest.TestCase):
    def setUp(self):
        self.program = analyze.Microcode(analyze.load_microcode_from_txt())

    def test_microcode_paths(self):
        with redirect_stdout(StringIO()):
            analyze.microcode_paths(self.program)

    def test_instruction_table(self):
        with redirect_stdout(StringIO()):
            analyze.instruction_table()

    def test_microcode_graph(self):
        with redirect_stdout(StringIO()):
            analyze.microcode_graph(self.program)

if __name__ == "__main__":
    unittest.main()
