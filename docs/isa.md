# NXNode ISA (v0.4)

## Encodings Table

<style>
table {
    font-family:monospace;
}
table th, table td {
    padding:3px;
}
table td, table th {
    text-align:center;
}
table td {
    border:1px solid #666;
}
table tr td:first-child, table tr th:first-child {
    text-align:right;
    border:none;
    padding-right:10px;
}
</style>
<table>
    <tr>
        <th>Instruction</th>
        <th>31</th>
        <th>30</th>
        <th>29</th>
        <th>28</th>
        <th>27</th>
        <th>26</th>
        <th>25</th>
        <th>24</th>
        <th>23</th>
        <th>22</th>
        <th>21</th>
        <th>20</th>
        <th>19</th>
        <th>18</th>
        <th>17</th>
        <th>16</th>
        <th>15</th>
        <th>14</th>
        <th>13</th>
        <th>12</th>
        <th>11</th>
        <th>10</th>
        <th>9</th>
        <th>8</th>
        <th>7</th>
        <th>6</th>
        <th>5</th>
        <th>4</th>
        <th>3</th>
        <th>2</th>
        <th>1</th>
        <th>0</th>
    </tr>
    <tr>
        <td>LOAD</td>
        <td colspan="3">000</td>
        <td colspan="5">RSVD</td>
        <td colspan="2">OFFSET</td>
        <td colspan="10">ADDRESS</td>
        <td colspan="1">SLOT</td>
        <td colspan="5">RSVD</td>
        <td colspan="3">TGT</td>
        <td colspan="3">RSVD</td>
    </tr>
    <tr>
        <td>STORE</td>
        <td colspan="3">001</td>
        <td colspan="5">RSVD</td>
        <td colspan="2">OFFSET</td>
        <td colspan="10">ADDRESS</td>
        <td colspan="1">SLOT</td>
        <td colspan="8">MASK</td>
        <td colspan="3">SRC</td>
    </tr>
    <tr>
        <td>BRANCH</td>
        <td colspan="3">010</td>
        <td colspan="1">MARK</td>
        <td colspan="3">COMP</td>
        <td colspan="1">IDLE</td>
        <td colspan="2">OFFSET</td>
        <td colspan="10">PC</td>
        <td colspan="3">RSVD</td>
        <td colspan="3">SRC_B</td>
        <td colspan="3">RSVD</td>
        <td colspan="3">SRC_A</td>
    </tr>
    <tr>
        <td>SEND</td>
        <td colspan="3">011</td>
        <td colspan="4">RSVD</td>
        <td colspan="1">TRIG</td>
        <td colspan="2">OFFSET</td>
        <td colspan="10">ADDRESS</td>
        <td colspan="1">SLOT</td>
        <td colspan="4">NODE_ROW</td>
        <td colspan="4">NODE_COL</td>
        <td colspan="3">SRC</td>
    </tr>
    <tr>
        <td>TRUTH</td>
        <td colspan="3">100</td>
        <td colspan="8">TABLE</td>
        <td colspan="1">SI</td>
        <td colspan="8">IMM</td>
        <td colspan="3">SRC_C</td>
        <td colspan="3">SRC_B</td>
        <td colspan="3">TGT</td>
        <td colspan="3">SRC_A</td>
    </tr>
    <tr>
        <td>ARITH</td>
        <td colspan="3">101</td>
        <td colspan="5">RSVD</td>
        <td colspan="2">OP</td>
        <td colspan="13">RSVD</td>
        <td colspan="3">SRC_B</td>
        <td colspan="3">TGT</td>
        <td colspan="3">SRC_A</td>
    </tr>
    <tr>
        <td>SHUFL</td>
        <td colspan="2">11</td>
        <td colspan="3">B7</td>
        <td colspan="3">B6</td>
        <td colspan="3">B5</td>
        <td colspan="3">B4</td>
        <td colspan="3">B3</td>
        <td colspan="3">B2</td>
        <td colspan="3">B1</td>
        <td colspan="3">B0</td>
        <td colspan="3">TGT</td>
        <td colspan="3">SRC</td>
    </tr>
</table>

## `LOAD` & `STORE`

These operations manipulate the data memory of the node, and share the following
fields:

 * `ADDRESS` - 10-bit address allows access to the entire 1024 entry memory;
 * `SLOT` - each memory entry is 32-bit, but the node handles this as 2x16-bit
   slots - this bit selects between the lower (`[15:0]`) and upper (`[31:16]`)
   slots;
 * `OFFSET` - each 16-bit slot is split into 2x8-bit sub-slots and this field
   controls which sub-slot is selected;

The `LOAD` instruction also has a 3-bit `TGT` register field, while the `STORE`
instruction has a 3-bit `SRC` register field. The `STORE` instruction also has
an 8-bit `MASK` field which controls which bits are updated in the sub-slot.

The encoding of the `OFFSET` field is as follows:

 * `2b00` - use the node's default offset mode (set by a `BRANCH` instruction);
 * `2b01` - use the inverse of the node's default state;
 * `2b10` - force use of the lower sub-slot;
 * `2b11` - force use of the upper sub-slot;

The full 12-bit address of the 8-bit element of the memory can be expressed as:

```
full_address = { ADDRESS[9:0], SLOT, OFFSET[1] ? OFFSET[0] : (OFFSET[0] ^ DEFAULT) };
```

## `BRANCH`

This operation allows the program counter to be manipulated, along with the
`IDLE` and default `SUBSLOT` state of the node:

 * `PC` - 10-bit target address to jump to if branch evaluates successfully;
 * `SRC_A` - 3-bit source register field as the first input to the comparison;
 * `SRC_B` - 3-bit source register field as the second input to the comparison;
 * `IDLE` - whether to set the node's `IDLE` bit if the branch is taken;
 * `COMP` - 3-bit selector as to the comparison to perform;
 * `OFFSET` - 2-bit mode to update the node's default `OFFSET`;
 * `MARK` - whether to update the re-trigger address when the branch is taken;

The encoding of the `COMP` field is as follows:

 * `3b000` - unconditional branch (`JUMP`);
 * `3b001` - unconditional branch after next trigger received (`WAIT`);
 * `3b010` - conditional branch if `SRC_A == SRC_B` (i.e. `BEQ`);
 * `3b011` - conditional branch if `SRC_A != SRC_B` (i.e. `BNE`);
 * `3b100` - conditional branch if `SRC_A >= SRC_B` (i.e. `BGE`);
 * `3b101` - conditional branch if `SRC_A <  SRC_B` (i.e. `BLT`);
 * `3b110` - conditional branch if `SRC_A == 0` (i.e. `BEQZ`);
 * `3b111` - conditional branch if `SRC_A != 0` (i.e. `BNEZ`);

The encoding of the `OFFSET` field is similar to `LOAD` & `STORE`:

 * `2b00` - does not alter the node's default `OFFSET` state;
 * `2b01` - sets the node's default `OFFSET` state to the inverse of its current
   value;
 * `2b10` - forces the node's default `OFFSET` state to `0`;
 * `2b10` - forces the node's default `OFFSET` state to `1`;

## `SEND`

Queues up a 8-bit atom of data to send to any other node in the system:

 * `SRC` - 3-bit source register of data to send;
 * `NODE_ROW` - 4-bit row of the node to send to in the mesh;
 * `NODE_COL` - 4-bit column of the node to send to in the mesh;
 * `ADDRESS` - 10-bit address of the 32-bit memory entry in the target node;
 * `SLOT` - target slot selection (same as `STORE`, but targeting another node);
 * `OFFSET` - target sub-slot selection (same as `STORE`, but targeting another node);
 * `TRIG` - whether to re-trigger evaluation in the target node from the last mark;

## `TRUTH`

Performs logical operations on up to 3x8-bit sources:

 * `SRC_A`, `SRC_B`, `SRC_C` - input register selections;
 * `TGT` - target register selection;
 * `IMM` - 8-bit immediate;
 * `SI` - select between use of `IMM` (`1`) or `SRC_C` (`0`) as the third input;
 * `TABLE` - encoded truth table;

## `ARITH`

Perform arithmetic operations on 2x8-bit sources:

 * `SRC_A`, `SRC_B` - input register selections;
 * `TGT` - target register selection;
 * `OP` - 2-bit encoded operation to perform;

The encoding of the `OP` field is as follows:

 * `2b00` - perform `SRC_A + SRC_B`;
 * `2b01` - perform `SRC_A - SRC_B` (unsigned);
 * `2b10` - perform an `AND` reduction on `SRC_A` (e.g. `TGT = {8{&(SRC_A)}});`);
 * `2b10` - perform an `OR` reduction on `SRC_A` (e.g. `TGT = {8{|(SRC_A)}});`);

## `SHUFL`

Rearranges the bits of an source register into an arbitrary order:

 * `SRC` - input register selection;
 * `TGT` - target register selection;
 * `B[7-0]` - selection values for each bit in the target register from each bit
   in the source register.

Note that this register overloads bit 29 from being the operation encoding, to
being the MSB of the `B7` mux control.
