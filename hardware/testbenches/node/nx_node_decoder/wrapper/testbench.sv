// Copyright 2021, Peter Birch, mailto:peter@lightlogic.co.uk
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
    , parameter RAM_ADDR_W = 10
    , parameter RAM_DATA_W = 32
) (
      input  logic                        rst
    // Control signals
    , output logic                        o_idle
    // Inbound message stream
    , input  node_message_t               i_msg_data
    , input  logic                        i_msg_valid
    , output logic                        o_msg_ready
    // Write interface to node's memory (driven by node_load_t)
    , output logic [RAM_ADDR_W-1:0]       o_ram_addr
    , output logic [RAM_DATA_W-1:0]       o_ram_wr_data
    , output logic                        o_ram_wr_en
    // Input signal state (driven by node_signal_t)
    , output logic [$clog2(INPUTS)-1:0]   o_input_index
    , output logic                        o_input_value
    , output logic                        o_input_is_seq
    , output logic                        o_input_update
    // Control parameters (driven by node_control_t)
    , output logic [NODE_PARAM_WIDTH-1:0] o_num_instr
    , output logic [INPUTS-1:0]           o_loopback_mask
);

// =============================================================================
// Clock Generation
// =============================================================================

reg clk = 1'b0;
always #1 clk <= ~clk;

// =============================================================================
// DUT Instance
// =============================================================================

nx_node_decoder #(
      .INPUTS          ( INPUTS          )
    , .RAM_ADDR_W      ( RAM_ADDR_W      )
    , .RAM_DATA_W      ( RAM_DATA_W      )
) u_dut (
      .i_clk           ( clk             )
    , .i_rst           ( rst             )
    // Control signals
    , .o_idle          ( o_idle          )
    // Inbound message stream
    , .i_msg_data      ( i_msg_data      )
    , .i_msg_valid     ( i_msg_valid     )
    , .o_msg_ready     ( o_msg_ready     )
    // Write interface to node's memory (driven by node_load_t)
    , .o_ram_addr      ( o_ram_addr      )
    , .o_ram_wr_data   ( o_ram_wr_data   )
    , .o_ram_wr_en     ( o_ram_wr_en     )
    // Input signal state (driven by node_signal_t)
    , .o_input_index   ( o_input_index   )
    , .o_input_value   ( o_input_value   )
    , .o_input_is_seq  ( o_input_is_seq  )
    , .o_input_update  ( o_input_update  )
    // Control parameters (driven by node_control_t)
    , .o_num_instr     ( o_num_instr     )
    , .o_loopback_mask ( o_loopback_mask )
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
