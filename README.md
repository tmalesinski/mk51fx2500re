# Reverse Engineering the NEC D897G Calculator Chip

This is a project to reverse engineer the NEC D897G chip and its
Soviet clone К757ИП1-2 based on [die photos by Travis
Goodspeed](https://x.com/travisgoodspeed/status/1682510482647687168). The
NEC chip was used in Casio fx-2500 and fx-48 calculators. The Soviet
version was used in Elektronika MK-51 and MK-38.

The code extracted from the die photos supports keyboard layouts both
of the larger fx-2500 and MK-51 calculators and the smaller fx-48 and
MK-38.

## Emulator

This repository contains a working emulator. It requires GTK3 and its
Python bindings. You also need to get the ROM contents from [a
neighboring repository](https://github.com/tmalesinski/mk51fx2500rom):

```
ln -s ../mk51fx2500rom/mk51fx2500rom.txt .
./gmk51.py
```

## Documentation

To learn more about the chips, see:

* [Hardware description](doc/hardware.md)
* [Instruction list](doc/instructions.md)

## Reading the Code

You can disassemble the code by running:

```
./analyze.py listing
```

This attempts to print the code in an order where related instructions
are close together. This is useful because every instruction stores
the address of the next one and branch addresses are very constrained
(see the documentation) so ordering by address does not lead to a
logical order.

You can also create a flow graph of instructions with Graphviz:

```
./analyze.py graph >code.dot
dot -Tsvg code.dot >code.svg
```

You should be able to view the resulting SVG file with a web browser.

You can also use annotations from the [neighboring
repository](https://github.com/tmalesinski/mk51fx2500rom):

```
./analyze.py graph -a ../mk51fx2500rom/annotations.txt >code.dot
dot -Tsvg code.dot >code.svg
```
