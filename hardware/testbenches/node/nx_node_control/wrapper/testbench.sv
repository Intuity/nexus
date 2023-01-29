// Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

module testbench
import NXConstants::*;
#(
      parameter INPUTS     = 32
    , parameter OUTPUTS    = 32
    , parameter RAM_ADDR_W = 10
    , parameter RAM_DATA_W = 32
    , parameter EXT_INPUTS =  1
) (
      input  logic                        rst
    // Control signals
    , input  node_id_t                    i_node_id
    , input  logic                        i_trace_en
    , input  logic                        i_trigger
    , output logic                        o_idle
    // Inputs from decoder
    , input  logic [INPUTS-1:0]           i_loopback_mask
    , input  logic [$clog2(INPUTS)-1:0]   i_input_index
    , input  logic                        i_input_value
    , input  logic                        i_input_is_seq
    , input  logic                        i_input_update
    , input  logic [NODE_PARAM_WIDTH-1:0] i_num_instr
    // Output message stream
    , output node_message_t               o_msg_data
    , output logic                        o_msg_valid
    , input  logic                        i_msg_ready
    // Interface to store
    , output logic [RAM_ADDR_W-1:0]       o_ram_addr
    , output logic                        o_ram_rd_en
    , input  logic [RAM_DATA_W-1:0]       i_ram_rd_data
    // Interface to logic core
    , output logic                        o_core_trigger
    , input  logic                        i_core_idle
    , output logic [INPUTS-1:0]           o_core_inputs
    , input  logic [OUTPUTS-1:0]          i_core_outputs
    // External inputs
    , input  logic                        i_ext_inputs_en
    , input  logic [INPUTS-1:0]           i_ext_inputs
);

// =============================================================================
// Clock Generation
// =============================================================================

reg clk = 1'b0;
always #1 clk <= ~clk;

// =============================================================================
// DUT Instance
// =============================================================================

nx_node_control #(
      .INPUTS          ( INPUTS          )
    , .OUTPUTS         ( OUTPUTS         )
    , .RAM_ADDR_W      ( RAM_ADDR_W      )
    , .RAM_DATA_W      ( RAM_DATA_W      )
    , .EXT_INPUTS      ( EXT_INPUTS      )
) u_dut (
      .i_clk           ( clk             )
    , .i_rst           ( rst             )
    // Control signals
    , .i_node_id       ( i_node_id       )
    , .i_trace_en      ( i_trace_en      )
    , .i_trigger       ( i_trigger       )
    , .o_idle          ( o_idle          )
    // Inputs from decoder
    , .i_loopback_mask ( i_loopback_mask )
    , .i_input_index   ( i_input_index   )
    , .i_input_value   ( i_input_value   )
    , .i_input_is_seq  ( i_input_is_seq  )
    , .i_input_update  ( i_input_update  )
    , .i_num_instr     ( i_num_instr     )
    // Output message stream
    , .o_msg_data      ( o_msg_data      )
    , .o_msg_valid     ( o_msg_valid     )
    , .i_msg_ready     ( i_msg_ready     )
    // Interface to store
    , .o_ram_addr      ( o_ram_addr      )
    , .o_ram_rd_en     ( o_ram_rd_en     )
    , .i_ram_rd_data   ( i_ram_rd_data   )
    // Interface to logic core
    , .o_core_trigger  ( o_core_trigger  )
    , .i_core_idle     ( i_core_idle     )
    , .o_core_inputs   ( o_core_inputs   )
    , .i_core_outputs  ( i_core_outputs  )
    // External inputs
    , .i_ext_inputs_en ( i_ext_inputs_en )
    , .i_ext_inputs    ( i_ext_inputs    )
);

// =============================================================================
// Tracing
// =============================================================================

`ifdef sim_icarus
initial begin : i_trace
    string f_name;
    $timeformat(-9, 2, " ns", 20);
    if ($value$plusargs("WAVE_FILE=%s", f_name)) begin
        $display("%0t: Capturing wave file %s", $time, f_name);
        $dumpfile(f_name);
        $dumpvars(0, testbench);
    end else begin
        $display("%0t: No filename provided - disabling wave capture", $time);
    end
end
`endif // sim_icarus

endmodule : testbench
