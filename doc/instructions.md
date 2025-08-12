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

op = 00000

branches: none

row addr: yes

Continues program execution at the next address. Ignores the field, so
it executes in one digit cycle without waiting for a specific
field. Useful to change the row part of the address after an
instruction that does not allow that.

## CALL adr

op = 00001

branches: none

row addr: yes

Format: `ttt 00001 uuuu rrrr ccc CCC`

Continues program execution at the next address. Pushes a return
address (`000 ttt uuuu`)to the stack. Ignores the field, so it
executes in one digit cycle without waiting for a specific field.

## INSH #i,Rd

op = 00010

branches: none

row addr: no

Shifts the field in Rd one digit to the right (towards less
significant digits) and puts `i` as the most significant digit in the
field.

## RETURN adr

op = 00011

branches: none

row addr: yes

Pops a return address from the stack and continues at an address equal
to the bitwise or of the adress from the stack and the next address
from the instruction (TODO: are all bits actually or'd?)

## MOV Rd,R1

op = 00100

branches: none

row addr: yes

Copies the field from Rd to the field in R1.

## MOV Rd,R0

op = 00101

branches: none

row addr: yes

Copies the field from Rd to the field in R0.

## AND #i,Rd

op = 00110

branches: none

row addr: no

Sets each digit in the field of Rd to bitwise and of the digit and
`i`.

TODO: KR0 when i == 0 and it is MOV KR0,Rd then (no and'ing)

## TST #i,Rd

op = 00111

branches: NZ

row addr: no

Computes bitwise and of each digit in the field of Rd and
`i`. Does not change Rd. Branches when any result is non-zero.

TODO: KR0 when i == 0 and it is just TST KR0 then (no and'ing anymore)

## ADD #i.L,Rd

op = 01000

branches: none

row addr: no

Adds the number `i` to the number in the field in Rd.

TODO: key when i == 0

## MOV #i.L,Rd

op = 01001

branches: none

row addr: no

Sets the number in the field in Rd to the number `i`.

TODO: CLR as shorthand?

## ADD #3.L,Rd

op = 01010

branches: C

row addr: no

Adds the number `i` to the number in the field in Rd. Branches when
the result overflows in the field.

TODO: key when i == 0

## CMPN #i.L,Rd

op = 01011

branches: C

row addr: no

Adds the number `i` and the number in the field in Rd. Does not change
Rd. Branches when the addition resulted in a carry.

TODO: key when i == 0

## SUB #i.L,Rd

TODO: make these into a table with header and one row?
op = 01100

branches: none

row addr: no

Subtracts the number `i` from the number in the field in Rd. Branches when
the operation result in a borrow.

TODO: key when i == 0

## OR #i,Rd

op = 01101

branches: none

row addr: no

Requires that the field is one digit long.

Sets the digit in the field of Rd to bitwise or of the digit and
`i`.

## INSL #i,Rd

op = 01101

branches: none

row addr: no

Requires that the field is longer than one digit

Shifts the field in Rd one digit to the left (towards more
significant digits) and puts `i` as the least significant digit in the
field.

## SHL Rd

The same as `INSL #0,Rd` (TODO: is it true when looking at the code?)

TODO: is it useful to have it as another instruction?

## SUB #i.L,Rd

op = 01110

branches: C,NZ

row addr: no

Subtracts the number `i` from the number in the field in Rd. Branches when
the operation result in a borrow or is non-zero.

TODO: key when i == 0

## CMP #i.L,Rd

op = 01111

branches: C,NZ

row addr: no

Subtracts the number `i` from the number in the field in Rd. Does not
change Rd. Branches when the operation results in a borrow or is non-zero.

TODO: key when i == 0

## ADD Rs,Rd

op = 1s000

branches: none

row addr: yes

Adds the number in the field of Rs to the number in the field in Rd.

## MOV Rs,Rd

op = 1s001

branches: none

row addr: yes

Sets the field in Rd to the number in the field of Rs.

## ADD Rs,Rd

op = 1s010

branches: C

row addr: yes

Adds the number in the field of Rs to the number in the field in
Rd. Branches when the result overflows the field.

## CMPN Rs,Rd

op = 1s011

branches: C

row addr: yes

Adds the number in the field of Rs and the number in the field in
Rd. Does not change Rd. Branches when the addition results in a
carry.

TODO: is this one used in the code?

## SUB Rs,Rd

op = 1s100

branches: none

row addr: yes

Subtracts the number in the field of Rs from the number in the field in
Rd.

## SWAP Rs,Rd

op = 1s101

branches: none

row addr: yes

Swaps the fields in Rs and Rd.

## SUB Rs,Rd

op = 1s110

branches: C,NZ

row addr: yes

Subtracts the number in the field of Rs from the number in the field in
Rd. Branches when the operation result in a borrow or is non-zero.

## CMP Rs,Rd

op = 1s111

branches: C,NZ

row addr: yes

Subtracts the number in the field of Rs from the number in the field
in Rd. Does not change Rd. Branches when the operation results in a
borrow or is non-zero.
