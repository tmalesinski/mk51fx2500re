# Instruction Set

TODO: general instruction format

TODO: address format

TODO: repeated vs non-repeated constants

TODO: field codes, decimal mode

TODO: branches (C and NZ)

TODO: say that mnemonics do not indicate branches (maybe they
should). Or just say (with branch on carry or nz when it's ambiguous)

TODO: disclaimer that it may not be correct because it is inferred
from the logic

TODO: say that syntax may change (no #?)

TODO: or just put everything into a table:
mnemonic, op, branches, row addr, constraints/requires, operation plus
explanation for a few instructions (JUMP, CALL, RETURN). And then
shorthands separately.

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

Format: `ttt 00001 uuuu rrrr ccc CCC`

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

Adds the key codes to the number in the field in Rd.

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

Adds the key codes to the number in the field in Rd. Branches when
the result overflows in the field.

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

Adds the key codes and the number in the field in Rd. Does not change
Rd. Branches when the addition resulted in a carry.

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

Subtracts the key codes from the number in the field in Rd. Branches when
the operation result in a borrow.

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

Subtracts the key codes from the number in the field in Rd. Branches when
the operation result in a borrow or is non-zero.

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

Subtracts the key codes from the number in the field in Rd. Does not
change Rd. Branches when the operation results in a borrow or is non-zero.

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
