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

`include "nx_common.svh"

// nexus
// Top-level of the Nexus simulation accelerator.
//
module nexus #(
      parameter ROWS           =   3
    , parameter COLUMNS        =   3
    , parameter STREAM_WIDTH   =  32
    , parameter ADDR_ROW_WIDTH =   4
    , parameter ADDR_COL_WIDTH =   4
    , parameter COMMAND_WIDTH  =   2
    , parameter INSTR_WIDTH    =  15
    , parameter INPUTS         =   8
    , parameter OUTPUTS        =   8
    , parameter REGISTERS      =   8
    , parameter MAX_INSTRS     = 512
    , parameter OPCODE_WIDTH   =   3
    , parameter COUNTER_WIDTH  =  32
) (
      input  wire clk_i
    , input  wire rst_i
    // Control signals
    , input  wire                     active_i
    , output wire [COUNTER_WIDTH-1:0] counter_o
    // Inbound stream
    , input  wire [STREAM_WIDTH-1:0] inbound_data_i
    , input  wire                    inbound_valid_i
    , output wire                    inbound_ready_o
    // Outbound stream
    , output wire [STREAM_WIDTH-1:0] outbound_data_o
    , output wire                    outbound_valid_o
    , input  wire                    outbound_ready_i
);

// Control signals
reg                      first_cycle;
reg                      trigger;
reg  [COUNTER_WIDTH-1:0] cycle;
wire                     mesh_idle;
reg                      idle_low;
wire [      COLUMNS-1:0] token_grant, token_release;

assign counter_o = cycle;

always @(posedge clk_i, posedge rst_i) begin : p_trigger
    if (rst_i) begin
        first_cycle <= 1'b1;
        trigger     <=  1'b0;
        cycle       <= {COUNTER_WIDTH{1'b0}};
        idle_low    <= 1'b0;
    end else begin
        first_cycle <= 1'b0;
        if (active_i && mesh_idle && idle_low) begin
            trigger  <= 1'b1;
            cycle    <= cycle + { {(COUNTER_WIDTH-1){1'b0}}, 1'b1 };
            idle_low <= 1'b0;
        end else begin
            trigger <= 1'b0;
            if (!mesh_idle) idle_low <= 1'b1;
        end
    end
end

// Drive the token grant signal
assign token_grant = first_cycle ? {COLUMNS{1'b1}} : token_release;

// Instance the mesh
nx_mesh #(
      .ROWS          (ROWS          )
    , .COLUMNS       (COLUMNS       )
    , .STREAM_WIDTH  (STREAM_WIDTH  )
    , .ADDR_ROW_WIDTH(ADDR_ROW_WIDTH)
    , .ADDR_COL_WIDTH(ADDR_COL_WIDTH)
    , .COMMAND_WIDTH (COMMAND_WIDTH )
    , .INSTR_WIDTH   (INSTR_WIDTH   )
    , .INPUTS        (INPUTS        )
    , .OUTPUTS       (OUTPUTS       )
    , .REGISTERS     (REGISTERS     )
    , .MAX_INSTRS    (MAX_INSTRS    )
    , .OPCODE_WIDTH  (OPCODE_WIDTH  )
) mesh (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Control signals
    , .trigger_i(trigger  )
    , .idle_o   (mesh_idle)
    // Token signals
    , .token_grant_i  (token_grant  )
    , .token_release_o(token_release)
    // Inbound stream
    , .inbound_data_i (inbound_data_i )
    , .inbound_valid_i(inbound_valid_i)
    , .inbound_ready_o(inbound_ready_o)
    // Outbound stream
    , .outbound_data_o (outbound_data_o )
    , .outbound_valid_o(outbound_valid_o)
    , .outbound_ready_i(outbound_ready_i)
);

endmodule : nexus
