class Program:
    def __init__(self, code):
        self._code = code

    @staticmethod
    def from_file(path="mk51dump.txt"):
        code = [0] * 1024
        with open("mk51dump.txt") as f:
            for i, line in enumerate(f.readlines()):
                line = line.strip()
                assert len(line) == 16 * 22, len(line)
                for r in range(16):
                    code[64 * r + i] = (int(line[r::16][::-1], base=2) ^
                                        ((1 << 22) - 1))
        return Program(code)

    def get(self, adr):
        return self._code[adr]
