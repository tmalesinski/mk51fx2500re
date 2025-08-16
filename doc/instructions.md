# Instruction Set

This document describes instructions supported by the chip. The
instructions were inferred from the logic that executes them so there
may be mistakes in this list. The chip does not have separate circuits
for each instruction listed here. For example, a MOV instruction
executes addition of zero to the source operand and stores the result
in the destination register. The SUB instruction is almost the same as
the ADD one, except that the carry bit is computed differently.

The emulator in this repository executes instructions in a way closer
to how the chip is actually implemented so it may be more correct.

## Instruction format

The length of an instruction word is 22 bits. The general format of an
instruction is:

```
21   18     13    9    5   2 0
 ddd  ooooo  ffff iiii ccc CCC
```

(bit 0 is the least significant one). The fields of an instruction
word are:

* d - the number of a serial register to operate on (some instructions can
  additionally access registers R0 and R1.
* o - 5-bit operation code, includes most of the information on the
  type of an operation that the instruction performs.
* f - 4-bit field code, defining the range of digits in a serial
  register to operate on.
* i - the immediate (constant) operand of an instruction or the row
  part of the address of the next instruction.
* c - the less significant column bits of the address of the next
  instruction.
* C - the more significant column bits of the address of the next
  instruction.

## Address format

The address format is:

```
adr = rrrrCCCccc
```

where:
*   `rrrr` is the 4-bit row address.
*   `CCC` and `ccc` are the respectively higher and lower halves of
    the 6-bit column address.

"Row" and "column" refer to rows and columns of the matrix of bits on
the chip die that implement the program ROM.

## Branches

An instruction may enable a branch on the carry or non-zero flag (or
both). For subtraction instructions borrow is used instead of carry.

If a branch on carry is enabled and the operation resulted in a carry,
bit 0 of the next instruction address is set to one.
If a branch on non-zero is enabled and the operation result was non-zero,
bit 1 of the next instruction address is set to one. If both
conditions are true, both bits are set.

Note that branches depend only on the result of the current
instruction. Flags are not preserved between instructions.

In the list below mnemonics do not indicate which branches are
enabled, even though many instructions exist in both branch and
no-branch versions. (TODO: put the possible branches in the mnemonics?)

## Fields

Instructions operating on serial registers work on a range of digits
in them called a field. The field code part of the instruction word
selects one of 12 fields. For some fields the field code also selects
if the operation will be performed using usual binary or decimal (BCD)
arithmetic.

In the table below, 0 is the least significant digit in a register. 14
is the most significant one. The ranges are inclusive on both ends.

| code | field | decimal |
| ---: | ----: | :-----: |
| 0000 | [0]   | no |
| 0001 | [13]  | no |
| 0010 | [12]  | no |
| 0011 | [2]   | no |
| 0100 | [14:0] | no |
| 0101 | [13:0] | no |
| 0110 | [14]  | no |
| 0111 | [11]  | no |
| 1000 | [1:0] | no |
| 1001 | [13:2] | no |
| 1010 | [12:0] | no |
| 1011 | [12:2] | no |
| 1100 | [1:0] | yes(*) |
| 1101 | [13:2] | yes |
| 1110 | [12:0] | yes |
| 1111 | [12:2] | yes |

(*) the decimal mode is probably disabled on digit 1.

## Immediate (constant) operands

Instructions that have an immediate operand do not store the row part
of the next instruction. It is the same as the row part of the current
instruction address.

On arithmetic instructions (ADD, SUB, CMP, CMPN, MOV) the immediate
operand is treated as a number. For example `ADD 5,R0 [12:2]` adds 5
to the number stored in the field [12:2] of R0.

For AND and TST instructions the mask that is applied to the register
has the immediate operand on each digit of the field. For example `AND
7,R1 [12:0]` will clear the most significant bit of each digit in the
field [12:0] of R0.

The OR instruction can only operate on single digit fields so there is
no ambiguity.

## Key codes

Key code that may be an input to an instruction can be considered as
another serial register. Digits 13 to 6 correspond to rows of the key
matrix (pins 40 to 47 of the chip). Depending on which key is pressed
in a row, its digit is set to:

| column pin | digit |
| ---------: | ----: |
| none       |     0 |
|         39 |     1 |
|         38 |     2 |
|         37 |     4 |
|         36 |     8 |
|         35 |     c |

## JUMP adr

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 00000 | none     | yes      |          |

Continues program execution at the next address. Ignores the field, so
it executes in one digit cycle without waiting for a specific
field. Useful to change the row part of the address after an
instruction that does not allow that.

## CALL adr

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 00001 | none     | yes      |          |

Format: `ttt 00001 uuuu iiii ccc CCC`

Continues program execution at the next address. Pushes a return
address (`000 ttt uuuu`)to the stack. Ignores the field, so it
executes in one digit cycle without waiting for a specific field.

## INSH #i,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 00010 | none     | no       |          |


Shifts the field in Rd one digit to the right (towards less
significant digits) and puts `i` as the most significant digit in the
field.

## RETURN adr

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 00011 | none     | yes      |          |

Pops a return address from the stack and continues at an address equal
to the bitwise or of the adress from the stack and the next address
from the instruction (TODO: are all bits actually or'd?)

## MOV Rd,R1

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 00100 | none     | yes      |          |

Copies the field from Rd to the field in R1.

## MOV Rd,R0

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 00101 | none     | yes      |          |

Copies the field from Rd to the field in R0.

## AND #i,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 00110 | none     | no       | i != 0   |

Sets each digit in the field of Rd to bitwise and of the digit and
`i`.

## MOV KR0,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 00110 | none     | no       | i = 0    |

For each key row probably sets all bits in the corresponding digit in
the field to the lowest bit of the key code. No instructions using KR0
are in the calculator code.

## TST #i,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 00111 | NZ       | no       | i != 0   |

Computes bitwise and of each digit in the field of Rd and
`i`. Does not change Rd. Branches when any result is non-zero.

## TST KR0

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 00111 | NZ       | no       | i = 0    |

Branches if for any key row in the field, the lowest bit of the key
code is one. No instructions using KR0 are in the calculator code.

## ADD #i,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 01000 | none     | no       | i != 0   |

Adds the number `i` to the number in the field in Rd.

## ADD KEY,R5

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 01000 | none     | no       | i = 0    |

Adds the field of the key code to the number in the field in Rd.

## MOV #i,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 01001 | none     | no       |          |

Sets the number in the field in Rd to the number `i`.

## CLR Rd

Shorthand for MOV 0,Rd.

## ADD #i,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 01010 | C        | no       | i != 0   |

Adds the number `i` to the number in the field in Rd. Branches when
the result overflows in the field.

## ADD KEY,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 01010 | C        | no       | i = 0    |

Adds the field of the key code to the number in the field in
Rd. Branches when the result overflows in the field.

## CMPN #i,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 01011 | C        | no       | i != 0   |

Adds the number `i` and the number in the field in Rd. Does not change
Rd. Branches when the addition resulted in a carry.

## CMPN KEY,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 01011 | C        | no       | i = 0    |

Adds the field of the key code and the number in the field in Rd. Does
not change Rd. Branches when the addition resulted in a carry.

## SUB #i,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 01100 | none     | no       | i != 0   |

Subtracts the number `i` from the number in the field in Rd. Branches when
the operation result in a borrow.

## SUB KEY,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 01100 | none     | no       | i = 0    |

Subtracts the field in the key code from the number in the field in
Rd. Branches when the operation result in a borrow.

## OR #i,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 01101 | none     | no       | len(field) = 1 |

Sets the digit in the field of Rd to bitwise or of the digit and
`i`.

## INSL #i,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 01101 | none     | no       | len(field) > 1 |

Shifts the field in Rd one digit to the left (towards more
significant digits) and puts `i` as the least significant digit in the
field.

## SHL Rd

The same as `INSL #0,Rd`

TODO: add SHR to analyze.py

## SUB #i,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 01110 | C,NZ     | no       | i != 0   |

Subtracts the number `i` from the number in the field in Rd. Branches when
the operation result in a borrow or is non-zero.

## SUB KEY,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 01110 | C,NZ     | no       | i = 0    |

Subtracts the field of the key code from the number in the field in
Rd. Branches when the operation result in a borrow or is non-zero.

## CMP #i,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 01111 | C,NZ     | no       | i != 0   |

Subtracts the number `i` from the number in the field in Rd. Does not
change Rd. Branches when the operation results in a borrow or is non-zero.

## CMP KEY,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 01111 | C,NZ     | no       | i = 0    |

Subtracts the field of the key code from the number in the field in
Rd. Does not change Rd. Branches when the operation results in a
borrow or is non-zero.

## ADD Rs,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 1s000 | none     | yes      |          |

Adds the number in the field of Rs to the number in the field in Rd.

## MOV Rs,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 1s001 | none     | yes      |          |

Sets the field in Rd to the number in the field of Rs.

## ADD Rs,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 1s010 | C        | yes      |          |

Adds the number in the field of Rs to the number in the field in
Rd. Branches when the result overflows the field.

## CMPN Rs,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 1s011 | C        | yes      |          |

Adds the number in the field of Rs and the number in the field in
Rd. Does not change Rd. Branches when the addition results in a
carry.

## SUB Rs,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 1s100 | none     | yes      |          |

Subtracts the number in the field of Rs from the number in the field in
Rd.

## SWAP Rs,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 1s101 | none     | yes      |          |

Swaps the fields in Rs and Rd.

## SUB Rs,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 1s110 | C,NZ     | yes      |          |

Subtracts the number in the field of Rs from the number in the field in
Rd. Branches when the operation result in a borrow or is non-zero.

## CMP Rs,Rd

| op    | branches | row addr | requires |
| :---: | :------: | :------: | :------: |
| 1s111 | C,NZ     | yes      |          |

Subtracts the number in the field of Rs from the number in the field
in Rd. Does not change Rd. Branches when the operation results in a
borrow or is non-zero.
