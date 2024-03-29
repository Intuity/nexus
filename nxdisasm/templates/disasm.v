<%doc>
Copyright 2021, Peter Birch, mailto:peter@lightlogic.co.uk

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
</%doc>
module Top (
      input  wire clk
    , input  wire rst
%for name, bits in outputs.items():
    , output wire [${len(bits)-1}:0] ${verilog_safe(name)}
%endfor
);

%for row, columns in enumerate(nodes):
    %for col, instrs in enumerate(columns):
// =============================================================================
// Row ${f"{row:03d}"}, Column ${f"{col:03d}"}
// =============================================================================

// Input Construction
<%
        stateful = []
        loopback = []
%>\
        %for idx in range(cfg_nd_ins):
            %if idx not in node_inputs[row][col]:
wire r${row}_c${col}_input_${idx} = 1'b0;
            %else:
<%
                src_row, src_col, src_pos, state, is_lb = node_inputs[row][col][idx]
                src_instr_idx = node_outputs[src_row][src_col][src_pos]
                if is_lb:
                    loopback.append((idx, src_instr_idx))
                elif state:
                    stateful.append((idx, src_row, src_col, src_instr_idx))
%>\
                %if is_lb or state:
reg  r${row}_c${col}_input_${idx};
                %else:
wire r${row}_c${col}_input_${idx} = r${src_row}_c${src_col}_instr_${src_instr_idx};
                %endif
            %endif ## idx not in node_inputs[row][col]
        %endfor ## idx in range(cfg_nd_ins)
        %if instrs:

// Instruction Sequence
<%          reg_state = [0] * cfg_nd_regs %>\
            %for idx, instr in enumerate(instrs):
wire r${row}_c${col}_instr_${idx} = \
                %if is_inverting(instr):
!\
                %else:
 \
                %endif ## is_inverting(instr.op)
(\
                %if instr.src_a_ip:
r${row}_c${col}_input_${instr.src_a}\
                %else:
r${row}_c${col}_instr_${reg_state[instr.src_a]}\
                %endif ## instr.src_a_ip
                %if verilog_op(instr) != "!":
 ${verilog_op(instr)} \
                    %if instr.src_b_ip:
r${row}_c${col}_input_${instr.src_b}\
                    %else:
r${row}_c${col}_instr_${reg_state[instr.src_b]}\
                    %endif ## instr.src_b_ip
                %else:
                \
                %endif ## verilog_op(instr) != "!"
); // TT: ${f"{instr.truth:08b}"}
<%              reg_state[instr.tgt_reg] = idx %>\
            %endfor ## idx, instr in enumerate(instrs)

// Generated outputs
wire [${cfg_nd_outs-1}:0] r${row}_c${col}_outputs_next;
            %for out_idx in range(cfg_nd_outs):
assign r${row}_c${col}_outputs_next[${out_idx}] = \
                %if out_idx in node_outputs[row][col]:
r${row}_c${col}_instr_${node_outputs[row][col][out_idx]};
                %else:
1'b0;
                %endif ## out_idx in node_outputs[row][col]
            %endfor ## out_idx in range(cfg_nd_outs)
        %endif ## instrs
        %if stateful or instrs:

// Stateful Behaviour
reg  [${cfg_nd_outs-1}:0] r${row}_c${col}_outputs;
always @(posedge clk, posedge rst) begin : p_r${row}_c${col}_state
    if (rst) begin
            %for idx, _ in loopback:
        r${row}_c${col}_input_${idx} <= 1'b0;
            %endfor ## idx, _ in loopback
            %for idx, _, _, _ in stateful:
        r${row}_c${col}_input_${idx} <= 1'b0;
            %endfor ## idx in stateful
        r${row}_c${col}_outputs <= ${cfg_nd_outs}'d0;
    end else begin
            %if loopback:
        // Loopbacks
            %endif
            %for idx, src_instr_idx in loopback:
        r${row}_c${col}_input_${idx} <= r${row}_c${col}_instr_${src_instr_idx};
            %endfor ## idx, src_instr_idx in loopback
            %if stateful:
        // Cross-node state
            %endif
            %for idx, src_row, src_col, src_instr_idx in stateful:
        r${row}_c${col}_input_${idx} <= r${src_row}_c${src_col}_instr_${src_instr_idx};
            %endfor ## idx, src_row, src_col, src_instr_idx in stateful
        // Register outputs
        r${row}_c${col}_outputs <= r${row}_c${col}_outputs_next;
    end
end
        %endif ## stateful or instrs

    %endfor ## col, instr in enumerate(columns)
%endfor ## row, columns in enumerate(nodes)
// =============================================================================
// Boundary Output Mapping
// =============================================================================
%for name, bits in outputs.items():
    %for idx, (src_row, src_col, src_idx, is_seq) in bits.items():
        %if is_seq:
reg ${verilog_safe(name)}_${idx}_q;
always @(posedge clk, posedge rst) ${verilog_safe(name)}_${idx}_q <= rst ? 1'b0 : r${src_row}_c${src_col}_outputs[${src_idx}];
assign ${verilog_safe(name)}[${idx}] = ${verilog_safe(name)}_${idx}_q;
        %else:
assign ${verilog_safe(name)}[${idx}] = r${src_row}_c${src_col}_outputs[${src_idx}];
        %endif

    %endfor
%endfor

endmodule
