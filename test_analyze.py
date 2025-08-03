#!/usr/bin/python3

import contextlib, io, unittest
from contextlib import redirect_stdout
from io import StringIO

import analyze
from program import Program

class TestAnalyze(unittest.TestCase):
    def setUp(self):
        self.program = Program.from_file()

    def test_program_paths(self):
        with redirect_stdout(StringIO()):
            analyze.program_paths(self.program)

    def test_instruction_table(self):
        with redirect_stdout(StringIO()):
            analyze.instruction_table()

    def test_program_graph(self):
        with redirect_stdout(StringIO()):
            analyze.program_graph(self.program)

if __name__ == "__main__":
    unittest.main()
