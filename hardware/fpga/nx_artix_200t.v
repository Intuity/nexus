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

// nx_artix_200t
// Nexus 7 instance for the Artix-7 XC7A200T
//
module nx_artix_200t #(
      parameter AXI4_DATA_WIDTH =                  64
    , parameter AXI4_STRB_WIDTH = AXI4_DATA_WIDTH / 8
    , parameter AXI4_ID_WIDTH   =                   1
) (
      input  wire clk
    , input  wire rstn
    // Status
    , output wire status_active
    , output wire status_idle
    , output wire status_trigger
    // Inbound AXI4-stream
    , input  wire [AXI4_DATA_WIDTH-1:0] inbound_tdata
    , input  wire [AXI4_STRB_WIDTH-1:0] inbound_tkeep
    , input  wire [AXI4_STRB_WIDTH-1:0] inbound_tstrb
    , input  wire [  AXI4_ID_WIDTH-1:0] inbound_tid
    , input  wire                       inbound_tlast
    , input  wire                       inbound_tvalid
    , output wire                       inbound_tready
    // Outbound AXI4-stream
    , output wire [AXI4_DATA_WIDTH-1:0] outbound_tdata
    , output wire [AXI4_STRB_WIDTH-1:0] outbound_tkeep
    , output wire [AXI4_STRB_WIDTH-1:0] outbound_tstrb
    , output wire [  AXI4_ID_WIDTH-1:0] outbound_tid
    , output wire                       outbound_tlast
    , output wire                       outbound_tvalid
    , input  wire                       outbound_tready
);

// Instance FIFO to support decode of inbound stream
wire [AXI4_DATA_WIDTH-1:0] buff_ib_data;
wire [AXI4_STRB_WIDTH-1:0] buff_ib_strobe;
wire                       buff_ib_valid;
reg                        buff_ib_pop;

wire ib_fifo_full, ib_fifo_empty;

assign buff_ib_valid  = !ib_fifo_empty;
assign inbound_tready = !ib_fifo_full;

nx_fifo #(
      .DEPTH(2)
    , .WIDTH(AXI4_DATA_WIDTH + AXI4_STRB_WIDTH)
) ib_fifo (
      .clk_i( clk )
    , .rst_i(~rstn)
    // Write interface
    , .wr_data_i({ inbound_tdata, inbound_tkeep & inbound_tstrb })
    , .wr_push_i(inbound_tvalid && !ib_fifo_full)
    // Read interface
    , .rd_data_o({ buff_ib_data, buff_ib_strobe })
    , .rd_pop_i (buff_ib_pop)
    // Status
    , .level_o(             )
    , .empty_o(ib_fifo_empty)
    , .full_o (ib_fifo_full )
);

// Control inbound
reg [30:0] ctrl_ib_data,  ctrl_ib_data_q;
reg        ctrl_ib_valid, ctrl_ib_valid_q;
wire       ctrl_ib_ready;

// Control outbound
wire [30:0] ctrl_ob_data;
wire        ctrl_ob_valid, ctrl_ob_ready;

// Mesh inbound
reg [30:0] mesh_ib_data,  mesh_ib_data_q;
reg        mesh_ib_valid, mesh_ib_valid_q;
wire       mesh_ib_ready;

// Mesh outbound
wire [30:0] mesh_ob_data;
wire        mesh_ob_valid, mesh_ob_ready;

// Inbound stream decode
reg decode_high, decode_high_q;

always @(*) begin : p_decode
    reg        is_ctrl;
    reg [30:0] payload;
    reg [ 3:0] strobe;

    // Initialise decode
    decode_high = decode_high_q;

    // Control inbound
    ctrl_ib_data  = ctrl_ib_data_q;
    ctrl_ib_valid = ctrl_ib_valid_q;

    // Mesh inbound
    mesh_ib_data  = mesh_ib_data_q;
    mesh_ib_valid = mesh_ib_valid_q;

    // Always clear pop
    buff_ib_pop = 1'b0;

    // If control is ready, clear valid
    if (ctrl_ib_ready) ctrl_ib_valid = 1'b0;

    // If mesh is ready, clear valid
    if (mesh_ib_ready) mesh_ib_valid = 1'b0;

    // If both valid signals are clear, perform the next decode
    if (!ctrl_ib_valid && !mesh_ib_valid) begin
        // If decode high is set, decode the upper 32-bits
        { is_ctrl, payload } = decode_high ? buff_ib_data[63:32] : buff_ib_data[31:0];
        strobe               = decode_high ? buff_ib_strobe[7:4] : buff_ib_strobe[3:0];

        // If stream is valid, perform an action
        if (buff_ib_valid && strobe == 4'hF) begin
            // Provide payload to both control & mesh
            ctrl_ib_data = payload;
            mesh_ib_data = payload;

            // Set the correct valid signal
            ctrl_ib_valid =  is_ctrl;
            mesh_ib_valid = !is_ctrl;

            // If decode high or upper bytes are not populated, pop entry
            buff_ib_pop = (decode_high == 1'b1) || (buff_ib_strobe[7:4] != 4'hF);

            // Alternate to decode high if upper bytes are populated
            decode_high = (decode_high == 1'b0) && (buff_ib_strobe[7:4] == 4'hF);

        end else begin
            decode_high = 1'b0;

        end

    end
end

always @(posedge clk, negedge rstn) begin : p_decode_seq
    if (!rstn) begin
        decode_high_q   <=  1'b0;
        ctrl_ib_data_q  <= 31'd0;
        ctrl_ib_valid_q <=  1'b0;
        mesh_ib_data_q  <= 31'd0;
        mesh_ib_valid_q <=  1'b0;
    end else begin
        decode_high_q   <= decode_high;
        ctrl_ib_data_q  <= ctrl_ib_data;
        ctrl_ib_valid_q <= ctrl_ib_valid;
        mesh_ib_data_q  <= mesh_ib_data;
        mesh_ib_valid_q <= mesh_ib_valid;
    end
end

// Nexus instance
nexus #(
      .ROWS          (  6)
    , .COLUMNS       (  6)
    , .ADDR_ROW_WIDTH(  4)
    , .ADDR_COL_WIDTH(  4)
    , .COMMAND_WIDTH (  2)
    , .INSTR_WIDTH   ( 15)
    , .INPUTS        (  8)
    , .OUTPUTS       (  8)
    , .REGISTERS     (  8)
    , .MAX_INSTRS    (512)
    , .OPCODE_WIDTH  (  3)
) core (
      .clk_i( clk )
    , .rst_i(~rstn)
    // Status signals
    , .status_active_o (status_active )
    , .status_idle_o   (status_idle   )
    , .status_trigger_o(status_trigger)
    // Control message streams
    // - Inbound
    , .ctrl_ib_data_i (ctrl_ib_data )
    , .ctrl_ib_valid_i(ctrl_ib_valid)
    , .ctrl_ib_ready_o(ctrl_ib_ready)
    // - Outbound
    , .ctrl_ob_data_o (ctrl_ob_data )
    , .ctrl_ob_valid_o(ctrl_ob_valid)
    , .ctrl_ob_ready_i(ctrl_ob_ready)
    // Mesh message streams
    // - Inbound
    , .mesh_ib_data_i (mesh_ib_data )
    , .mesh_ib_valid_i(mesh_ib_valid)
    , .mesh_ib_ready_o(mesh_ib_ready)
    // - Outbound
    , .mesh_ob_data_o (mesh_ob_data )
    , .mesh_ob_valid_o(mesh_ob_valid)
    , .mesh_ob_ready_i(mesh_ob_ready)
);

// Outbound FIFO
wire [63:0] ob_fifo_data;
wire        ob_fifo_full, ob_fifo_empty;

assign outbound_tdata  = { 1'b1, ob_fifo_data[62:32], 1'b0, ob_fifo_data[30:0] };
assign outbound_tstrb  = { {4{ob_fifo_data[63]}}, {4{ob_fifo_data[31]}} };
assign outbound_tkeep  = outbound_tstrb;
assign outbound_tid    = {AXI4_ID_WIDTH{1'b0}};
assign outbound_tlast  = 1'b1;
assign outbound_tvalid = !ob_fifo_empty;

assign ctrl_ob_ready = !ob_fifo_full;
assign mesh_ob_ready = !ob_fifo_full;

nx_fifo #(
      .DEPTH( 2)
    , .WIDTH(64)
) ob_fifo (
      .clk_i( clk )
    , .rst_i(~rstn)
    // Write interface
    , .wr_data_i({ ctrl_ob_valid, ctrl_ob_data, mesh_ob_valid, mesh_ob_data })
    , .wr_push_i((ctrl_ob_valid || mesh_ob_valid) && !ob_fifo_full)
    // Read interface
    , .rd_data_o(ob_fifo_data)
    , .rd_pop_i (!ob_fifo_empty && outbound_tready)
    // Status
    , .level_o(             )
    , .empty_o(ob_fifo_empty)
    , .full_o (ob_fifo_full )
);

endmodule : nx_artix_200t
