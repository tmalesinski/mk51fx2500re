class Microcode:
    def __init__(self, code):
        self._code = code

    @staticmethod
    def from_file(path="mk51dump.txt"):
        code = []
        with open("mk51dump.txt") as f:
            for line in f.readlines():
                line = line.strip()
                assert len(line) == 16 * 22, len(line)
                for r in range(16):
                    code.append(
                        int(line[r::16][::-1], base=2) ^ ((1 << 22) - 1))
        return Microcode(code)

    def get(self, adr):
        return self._code[adr]
