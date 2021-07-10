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

// Internal state
reg         active, active_q;
wire [31:0] counter;

// Status signals
assign status_active = active_q;

// Instance skid to support decode of inbound stream
wire [AXI4_DATA_WIDTH-1:0] skid_ib_data;
wire [AXI4_STRB_WIDTH-1:0] skid_ib_strobe;
wire [  AXI4_ID_WIDTH-1:0] skid_ib_id;
wire                       skid_ib_valid;
reg                        skid_ib_ready, skid_ib_ready_q;

nx_stream_skid #(
    .STREAM_WIDTH(AXI4_DATA_WIDTH + AXI4_STRB_WIDTH + AXI4_ID_WIDTH)
) skid_axi_ib (
      .clk_i( clk )
    , .rst_i(~rstn)
    // Inbound message stream
    , .inbound_data_i ({ inbound_tdata, inbound_tkeep & inbound_tstrb, inbound_tid })
    , .inbound_valid_i(inbound_tvalid)
    , .inbound_ready_o(inbound_tready)
    // Outbound message stream
    , .outbound_data_o ({ skid_ib_data, skid_ib_strobe, skid_ib_id })
    , .outbound_valid_o(skid_ib_valid)
    , .outbound_ready_i(skid_ib_ready)
);

// Core inbound
reg [31:0] core_ib_data,  core_ib_data_q;
reg        core_ib_valid, core_ib_valid_q;
wire       core_ib_ready;

// Control outbound
reg [31:0] ctrl_ob_data,  ctrl_ob_data_q;
reg        ctrl_ob_valid, ctrl_ob_valid_q;
wire       ctrl_ob_ready;

// Inbound stream decode
reg decode_high, decode_high_q;

always @(*) begin : p_decode
    reg        is_ctrl;
    reg [30:0] payload;
    reg [ 3:0] strobe;

    active        = active_q;
    skid_ib_ready = skid_ib_ready_q;
    core_ib_data  = core_ib_data_q;
    core_ib_valid = core_ib_valid_q;
    ctrl_ob_data  = ctrl_ob_data_q;
    ctrl_ob_valid = ctrl_ob_valid_q;
    decode_high   = decode_high_q;

    // If the core is ready, clear valid
    if (core_ib_ready) core_ib_valid = 1'b0;

    // If the outbound stream is ready, clear valid
    if (ctrl_ob_ready) ctrl_ob_valid = 1'b0;

    // If valid clear, attempt the next decode
    if (!core_ib_valid && !ctrl_ob_valid) begin
        // If decode high is set, decode the upper 32-bits
        { is_ctrl, payload } = decode_high ? skid_ib_data[63:32] : skid_ib_data[31:0];
        strobe               = decode_high ? skid_ib_strobe[7:4] : skid_ib_strobe[3:0];

        // If stream is valid, perform an action
        if (skid_ib_valid && strobe == 4'hF) begin
            // If is_ctrl, setup active and publish cycle count
            if (is_ctrl) begin
                active        = payload[0];
                ctrl_ob_data  = { 1'b1, counter[30:0] };
                ctrl_ob_valid = 1'b1;

            // If not set, redirect into the core
            end else begin
                core_ib_data  = { 1'b0, payload };
                core_ib_valid = 1'b1;

            end

            // Alternate decode high
            decode_high = ~decode_high;

        end else begin
            decode_high = 1'b0;

        end

        // If decode high is set, drop the ready (need 2nd decode cycle)
        skid_ib_ready = !decode_high;

    // Otherwise keep inbound ready low
    end else begin
        skid_ib_ready = 1'b0;

    end
end

always @(posedge clk, negedge rstn) begin
    if (!rstn) begin
        active_q        <=  1'b0;
        skid_ib_ready_q <=  1'b0;
        decode_high_q   <=  1'b0;
        core_ib_data_q  <= 32'd0;
        core_ib_valid_q <=  1'b0;
        ctrl_ob_data_q  <= 32'd0;
        ctrl_ob_valid_q <=  1'b0;
    end else begin
        active_q        <= active;
        skid_ib_ready_q <= skid_ib_ready;
        decode_high_q   <= decode_high;
        core_ib_data_q  <= core_ib_data;
        core_ib_valid_q <= core_ib_valid;
        ctrl_ob_data_q  <= ctrl_ob_data;
        ctrl_ob_valid_q <= ctrl_ob_valid;
    end
end

// Instance nexus
wire [31:0] core_ob_data;
wire        core_ob_valid, core_ob_ready;

nexus #(
      .ROWS          (  6)
    , .COLUMNS       (  6)
    , .STREAM_WIDTH  ( 32)
    , .ADDR_ROW_WIDTH(  4)
    , .ADDR_COL_WIDTH(  4)
    , .COMMAND_WIDTH (  2)
    , .INSTR_WIDTH   ( 15)
    , .INPUTS        (  8)
    , .OUTPUTS       (  8)
    , .REGISTERS     (  8)
    , .MAX_INSTRS    (512)
    , .OPCODE_WIDTH  (  3)
    , .COUNTER_WIDTH ( 32)
) core (
      .clk_i( clk )
    , .rst_i(~rstn)
    // Control signals
    , .active_i (active )
    , .counter_o(counter)
    // Inbound stream
    , .inbound_data_i (core_ib_data )
    , .inbound_valid_i(core_ib_valid)
    , .inbound_ready_o(core_ib_ready)
    // Outbound stream
    , .outbound_data_o (core_ob_data )
    , .outbound_valid_o(core_ob_valid)
    , .outbound_ready_i(core_ob_ready)
);

// Mux between the core and control output streams (control gets priority)
assign ctrl_ob_ready = outbound_tready;
assign core_ob_ready = outbound_tready && !ctrl_ob_valid_q;

assign outbound_tdata = {
    32'd0,                                 // 32-bit padding
    ctrl_ob_valid_q,                       // Bit 31 indicates control/core
    ctrl_ob_valid_q ? ctrl_ob_data_q[30:0] // Bits 30:0 carry payload
                    : core_ob_data[30:0]
};

assign outbound_tkeep  = 8'h0F;
assign outbound_tstrb  = 8'h0F;
assign outbound_tid    = {AXI4_ID_WIDTH{1'b0}};
assign outbound_tlast  = 1'b1;
assign outbound_tvalid = ctrl_ob_valid_q || core_ob_valid;

endmodule : nx_artix_200t
