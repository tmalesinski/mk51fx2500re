# Hardware Description

The chip in FX-2500 and MK-51 calculators is built using CMOS
technology. For an introduction to reverse engineering CMOS ICs, read
[this Ken Shirriff's blog
post](https://www.righto.com/2024/01/reverse-engineering-cmos.html).
It's particularly useful to know that transistors that pull high are
in a complementary circuit compared to those that pull low. While it
is quite easy to find transistors that are connected in series,
especially on the bottom layer, those wired in parallel are much less
clear and they often have to be deduced from the serial transistors on
the other side. Also note that although the chips in MK-51 and FX-2500
look very similar, their layouts do not align perfectly. Travis
Goodspeed posted an image of the bottom layer from FX-2500 but the top
layer is clearer on his photo from the MK-51. If you try to align
them, they will not match. Possibly the chip was copied by manually
redrawing the masks.

## General Architecture

The calculator chip has a serial architecture which means that it
processes data one bit at a time. For example, the adder circuit in
every cycle takes one bit from each input and produces one bit of the
result. Numbers that the calculator operates on are stored in eight 60
bit shift registers. This gives enough space to store up to 15 BCD
coded digits in one register. Bits in these registers are shifted
around countinuously. An instruction may operate on a selected range
of digits in the registers, which we'll call a field. To execute an
instruction, the control logic waits until the beginning of the field
is on the registers outputs and routes the selected registers to the
adder inputs. If the result is going to be stored in a register, the
result is routed to the input of that register. Inputs of the
remaining registers are connected to their outputs so that their
content is preserved. The instruction executes until the end of the
field.

This part is similar to HP-35 which is described in detail at
[Jacques Laporte's web site](https://archived.hpcalc.org/laporte/).

Unlike typical CPUs, the chip has no instruction pointer, at least not
a full one. Instead, each instruction contains the address of the next
one. Some instructions do not store one part of the address. In this
case this part of the address is stored in a register and is appended
to the rest of the address from the instruction.

The chip contains a 5-level return address stack for subroutines.

## Main Blocks

The following diagram shows the main blocks of the chip. We focus on
the blocks most important for understanding and emulating the
calculator's code, so large parts of the display logic or clock
generation are ignored.

![Chip block diagram](/img/mk51_described_small.jpg)


### Program ROM

The program is stored in a matrix consisting of 16*22 = 352 rows and
64 columns. Actually, there are 80 columns divided into groups of 5
but the bits in the fifth column of a group are all the same. This was
probably done to have a larger program space if needed. There are a
few not connected transistors that were likely supposed to select the
fifth column in specific circumstances (without adding one more
address bit). The program in its current version fits into the
unextended program space. There even seem to be a few free locations
in the memory.

An instruction word has 22 bits. One column stores bits for 16
instructions. In total the ROM has space for 1024 instructions
(ignoring the additional fifth columns).

Above the program ROM there is a column decoder selecting one of the
columns. Between the ROM and the instruction register there are
circuts (not marked on the image) selecting one of 16 rows for each
bit of an instruction.

We'll use the following convention to assign addresses:

```
adr = rrrrCCCccc
```

where:
*   `rrrr` is the 4-bit row address. Row 0 is the topmost one out of the
    16 rows connected to each instruction register bit.
*   `CCC` and `ccc` are the respectively higher and lower halves of
    the 6-bit column address. Column 0 is the rightmost one.
	
This assignment is a little arbitrary because there is no instruction
pointer that would be incremented after an instruction so there is no
natural order of the addresses or of the row and column address
bits. Given that not every instruction may select a new row address,
this part of the address tends to stay the same in related parts of
the code, so it makes sense to assign it to the most significant bits.

Travis Goodspeed in his ROM dump [assumed that the places that are
connected on the rows are
ones](https://x.com/travisgoodspeed/status/1683227297367638017). It
turns out it's better to assume that they are zeros. This way the
constant operands in instructions (like the digits of pi) are not
inverted.

### Instruction Register

It's a 22-bit register storing the instruction being executed. We'll
assume that the topmost bit on the image is the least significant one
(bit 0). This is consistent with the order of bits in the fields of
the instruction word that contain addresses, constants or register
numbers.

### Program Address Logic

The address of the next instruction may come from the current
instruction or from the return stack. It may be modified on branches.

The three higher column address bits are actually always connected to
three bits lowest bits of the instruction. In particualr, this means
that the return address from a subroutine is not fully set by the
`CALL` instruction. The three higher column bits are set in the
`RETURN` instruction. Other address bits may also be overridden to
ones by `RETURN` (TODO: can all bits be overridden or only the column
ones?). This way a subroutine can return to a few different
addresses. This saves a few instructions compared to setting a flag or
a register in the subroutine and then branching based on it in the
caller.

The part of the instruction that stores the row address of the next
instruction is also used to store constant (immediate) operands. So
instructions with a constant operand do not have a row address. The
row address in this case is taken from the register located right
above the program address logic. This register always stores the
current row address.

An instruction may enable branching on carry (or borrow for
subtraction) or the result being non zero. Branches on both flags may
be enabled on the same instruction. A branch on carry sets bit 0 of
the next address. A branch on non zero sets bit 1. This way a `CMP`
instruction may go to one of three instructions depending on the
comparison result. The flags are not preserved across instructions. A
branch always uses the result of the current instruction.

The way in which branches work puts constraints on the addresses at
which instructions are located. Because of that instructions are
rarely stored in the order in which they are executed. Exceptions here
are sequences of instructions that generate a constant like pi.

### Return Stack

The stack has 5 locations storing 7-bit return addresses (without the
higher part of the column address which always comes from the `RETURN`
instruction). There is a 3-bit stack pointer register. (TODO: does the
stack pointer wrap around?).

It seems to be implemented using a non-standard binary code, likely to
simplify the computation of the next and previous state. This detail
is not visible to the program.

### Instruction Decoder

The instruction decoder takes bits 14-18 of the instruction word and
generates a number of signals controlling various blocks, for example
whether the current instruction is a `CALL` instruction, a `RETURN`
or if it has the row part of the next instruction address. The decoder
also combines a few other inputs. For example, the branch signals
already take the corresponding flag into account, so they say whether
a branch should be taken and not only if the instruction enables
branching.

### Serial Registers

The chip stores the numbers that it operates on in eight 60 (15*4) bit
shift registers. The numbers are continuously rotated in these
registers. To write a new value to a register, new data is sent to the
input of the register instead of data from its output.

### Register Selector

The registers are numbered from 0 at the top to 7 at the bottom. Bits
19-21 of the instruction select one of the registers. It may be used
as one of the inputs and the output of an instruction. Registers 0 and
1 can also be used even when they are not selected this way.

The selector circuit outputs data from the selected register and also
generates write enable signals for each register.

### Bit and Digit Counters

The bit and digit counters keep track of the current position in the
serial registers. The bit counter counts bits within a digit (from 0
to 3). The digit counter counts digits (from 0 to 14).

The counters are implemented as
[LSFRs](https://en.wikipedia.org/wiki/Linear-feedback_shift_register). (TODO:
is it the case for the bit counter as well?). This detail is important
for tracing the logic dependent on their state but is not visible to
the program.

### Field Start/Stop Detector

An instruction operates on a range of digits in registers that we'll
call a field. There are 12 predefined fields, encoded in bits 10-13 of
the instruction. The field start/stop detector checks the state of the
digit counter and generates start and stop signals at the right
time. There are two registers storing the field state. One stores
whether the current digit is in the field, the other is a delayed stop
signal. 

Once the field of the current instruction finishes, the chip moves to
the next instruction. This means that during one rotation of serial
registers multiple instructions may be executed. Two subsequent
fields probably need to be separated by at least one digit to allow
that, though.

`CALL`, `RETURN`, and `JUMP` instructions do not wait for their
field. They (probably) always execute in one digit time.

### Adder Input Selector

Operands for the adder are selected in the adder input selector based
mostly on bits 14-18 of the instruction. Other signals used in the
input selection are whether the immediate (constant) operand is 0 or
if the field is one element long.

Logical AND and OR operations with a constant are also implemented in
the input selector. `MOV` instruction is implemented by setting one of
the inputs to 0. Setting both inputs to 0 gives a `CLR` instruction.

Possible inputs are:
*   the selected register
*   register 0 or 1
*   4-bit constant on the first or last digit of the field
*   the selected register masked with a 4-bit constant on all digits
*   key state (one digit for each row of the key matrix)
*   the selected register delayed by one digit (shifted left, towards
    the more significant digits)
*   zero
	
Only some combinations of inputs are supported.

### Key and Immediate Bit Selectors

These selector select the current bit according to the bit counter
from the immediate operand stored in bits 6-9 of the instruction or
from the key state code. These bits are provided to the adder input
selector.

### Adders

The adders compute sum or difference of their inputs.
They generate one bit of the result in each bit counter
cycle. Adder 1 adds or subtracts bits from the selected adder
inputs. The operation may optionally be performed in
[BCD](https://en.wikipedia.org/wiki/Binary-coded_decimal) where, for
example 6+7 is 3 (plus carry) instead of 0xd. For that adder 2 adds or
subtracts 6 from the result of the first adder when it's greater than 9
on addition or below 0 on subtraction. To decide whether the result of
adder 1 is greater than 9, it is buffered in a 3-bit shift register in
the adder state. The adder state also stores the carry and zero flags.

The BCD mode is enabled based on the field code. 4 of the 12 posible
fields can be used in binary or the BCD mode.

In addition and subtraction the result bits are computed in the same
way. Only carry computation is changed to borrow for subtraction.

### Register Routing

The result of the adders is passed to the register routing circuit
where it can be sent to the input of the selected register. Some
instructions do not store the result but compute it only for the
flags.

Additionally, the data from the selected register may be writted to
register 0 or 1. This is used to swap the contents of two registers or
to copy the value from the selected register to register 0 or 1.

The value from the selected register may also bypass the adders and
appear in the register routing earlier. This way digits can be shifted
to the right.

### Register Delays

To enable computations in BCD (decide whether a decimal correction is
necessary and apply it), the adder delays the result by a digit. The
delay is also present in the binary mode. To compensate for that, the
data from serial registers is passed through a 4-bit delay before it
is sent to their inputs.

The delay for register 0 is not among the eight other delays. It is
instead to the left and serves as a display buffer. One delay among
the eight similar ones is a delay for the selected register and it is
used to implement shifting a number left.

### Display Buffer

The digit stored in the register 0 delay register is passed to the 7
segment decoder. In addition to digits 0 to 9, digit 0xd shown as "E"
and digit 0xe as "-".

The decimal point and mode indicators are driven from the two most
significant bits of digits in register 1.

The display circuit is only enabled when the current row address is
0xf.
