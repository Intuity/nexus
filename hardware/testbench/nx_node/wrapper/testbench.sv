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

module testbench #(
      parameter STREAM_WIDTH   =  32
    , parameter ADDR_ROW_WIDTH =   4
    , parameter ADDR_COL_WIDTH =   4
    , parameter COMMAND_WIDTH  =   2
    , parameter INSTR_WIDTH    =  15
    , parameter INPUTS         =   8
    , parameter OUTPUTS        =   8
    , parameter REGISTERS      =   8
    , parameter MAX_INSTRS     = 512
    , parameter OPCODE_WIDTH   =   3
) (
      input  logic rst
    // Control signals
    , input  logic                      trigger_i
    , output logic                      idle_o
    , input  logic [ADDR_ROW_WIDTH-1:0] node_row_i
    , input  logic [ADDR_COL_WIDTH-1:0] node_col_i
    // Inbound interfaces
    // - North
    , input  logic [STREAM_WIDTH-1:0] ib_north_data_i
    , input  logic                    ib_north_valid_i
    , output logic                    ib_north_ready_o
    // - East
    , input  logic [STREAM_WIDTH-1:0] ib_east_data_i
    , input  logic                    ib_east_valid_i
    , output logic                    ib_east_ready_o
    // - South
    , input  logic [STREAM_WIDTH-1:0] ib_south_data_i
    , input  logic                    ib_south_valid_i
    , output logic                    ib_south_ready_o
    // - West
    , input  logic [STREAM_WIDTH-1:0] ib_west_data_i
    , input  logic                    ib_west_valid_i
    , output logic                    ib_west_ready_o
    // Outbound interfaces
    // - North
    , output logic [STREAM_WIDTH-1:0] ob_north_data_o
    , output logic                    ob_north_valid_o
    , input  logic                    ob_north_ready_i
    , input  logic                    ob_north_present_i
    // - East
    , output logic [STREAM_WIDTH-1:0] ob_east_data_o
    , output logic                    ob_east_valid_o
    , input  logic                    ob_east_ready_i
    , input  logic                    ob_east_present_i
    // - South
    , output logic [STREAM_WIDTH-1:0] ob_south_data_o
    , output logic                    ob_south_valid_o
    , input  logic                    ob_south_ready_i
    , input  logic                    ob_south_present_i
    // - West
    , output logic [STREAM_WIDTH-1:0] ob_west_data_o
    , output logic                    ob_west_valid_o
    , input  logic                    ob_west_ready_i
    , input  logic                    ob_west_present_i
);

reg clk = 1'b0;
always #1 clk <= ~clk;

nx_node #(
      .STREAM_WIDTH  (STREAM_WIDTH  )
    , .ADDR_ROW_WIDTH(ADDR_ROW_WIDTH)
    , .ADDR_COL_WIDTH(ADDR_COL_WIDTH)
    , .COMMAND_WIDTH (COMMAND_WIDTH )
    , .INSTR_WIDTH   (INSTR_WIDTH   )
    , .INPUTS        (INPUTS        )
    , .OUTPUTS       (OUTPUTS       )
    , .REGISTERS     (REGISTERS     )
    , .MAX_INSTRS    (MAX_INSTRS    )
    , .OPCODE_WIDTH  (OPCODE_WIDTH  )
) dut (
      .clk_i(clk)
    , .rst_i(rst)
    // Control signals
    , .trigger_i (trigger_i )
    , .idle_o    (idle_o    )
    , .node_row_i(node_row_i)
    , .node_col_i(node_col_i)
    // Inbound interfaces
    // - North
    , .ib_north_data_i (ib_north_data_i )
    , .ib_north_valid_i(ib_north_valid_i)
    , .ib_north_ready_o(ib_north_ready_o)
    // - East
    , .ib_east_data_i (ib_east_data_i )
    , .ib_east_valid_i(ib_east_valid_i)
    , .ib_east_ready_o(ib_east_ready_o)
    // - South
    , .ib_south_data_i (ib_south_data_i )
    , .ib_south_valid_i(ib_south_valid_i)
    , .ib_south_ready_o(ib_south_ready_o)
    // - West
    , .ib_west_data_i (ib_west_data_i )
    , .ib_west_valid_i(ib_west_valid_i)
    , .ib_west_ready_o(ib_west_ready_o)
    // Outbound interfaces
    // - North
    , .ob_north_data_o   (ob_north_data_o   )
    , .ob_north_valid_o  (ob_north_valid_o  )
    , .ob_north_ready_i  (ob_north_ready_i  )
    , .ob_north_present_i(ob_north_present_i)
    // - East
    , .ob_east_data_o   (ob_east_data_o   )
    , .ob_east_valid_o  (ob_east_valid_o  )
    , .ob_east_ready_i  (ob_east_ready_i  )
    , .ob_east_present_i(ob_east_present_i)
    // - South
    , .ob_south_data_o   (ob_south_data_o   )
    , .ob_south_valid_o  (ob_south_valid_o  )
    , .ob_south_ready_i  (ob_south_ready_i  )
    , .ob_south_present_i(ob_south_present_i)
    // - West
    , .ob_west_data_o   (ob_west_data_o   )
    , .ob_west_valid_o  (ob_west_valid_o  )
    , .ob_west_ready_i  (ob_west_ready_i  )
    , .ob_west_present_i(ob_west_present_i)
);

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
