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

`timescale 1ns/1ps

module testbench();

// Generate 500 MHz clock
logic clk = 1'b0;
always begin
    #1ns clk = ~clk;
end

// Generate reset signal
logic rst;
initial begin : i_reset
    $display("%0t: Asserting reset", $time);
    rst = 1'b1;
    repeat (20) @(posedge clk);
    $display("%0t: De-asserting reset", $time);
    rst = 1'b0;
    repeat (10000) @(posedge clk);
    $fatal(1, "Timed out");
    $finish;
end

// External controls
logic m_tick;

always @(posedge clk) begin : p_gen_tick
    m_tick <= (!rst && m_in_wait && !m_tx_cmd_valid && m_rx_cmd_ready);
end

// State outputs
logic m_in_setup;
logic m_in_wait;
logic m_in_run;

// Inbound command
logic [7:0] m_rx_cmd_data;
logic       m_rx_cmd_last;
logic       m_rx_cmd_valid;
logic       m_rx_cmd_ready;

// Host commands
logic [7:0] m_host_data;
logic       m_host_last;
logic       m_host_valid;
logic       m_host_ready;

// Outbound command
logic [7:0] m_tx_cmd_data;
logic       m_tx_cmd_last;
logic       m_tx_cmd_valid;
logic       m_tx_cmd_ready;

// Node instance
nx_node #(
    // Command interface parameters
      .TARGET_W(8)
    , .CMD_W   (8)
    // Logic core parameters
    , .OP_W ( 4)
    , .REG_W(16)
    , .IO_W ( 4)
    , .SLOTS(32)
) m_dut (
      .clk(clk)
    , .rst(rst)
    // External controls
    , .tick(m_tick)
    // State outputs
    , .in_setup(m_in_setup)
    , .in_wait (m_in_wait )
    , .in_run  (m_in_run  )
    // Inbound command
    , .rx_cmd_data (m_rx_cmd_data )
    , .rx_cmd_last (m_rx_cmd_last )
    , .rx_cmd_valid(m_rx_cmd_valid)
    , .rx_cmd_ready(m_rx_cmd_ready)
    // Outbound command
    , .tx_cmd_data (m_tx_cmd_data )
    , .tx_cmd_last (m_tx_cmd_last )
    , .tx_cmd_valid(m_tx_cmd_valid)
    , .tx_cmd_ready(m_tx_cmd_ready)
);

// Command stream arbiter
nx_arbiter #(
    .BUS_W(8)
) m_arb (
      .clk(clk)
    , .rst(rst)
    // Inbound interface A
    , .inbound_a_data (m_tx_cmd_data )
    , .inbound_a_last (m_tx_cmd_last )
    , .inbound_a_valid(m_tx_cmd_valid)
    , .inbound_a_ready(m_tx_cmd_ready)
    // Inbound interface B
    , .inbound_b_data (m_host_data )
    , .inbound_b_last (m_host_last )
    , .inbound_b_valid(m_host_valid)
    , .inbound_b_ready(m_host_ready)
    // Outbound interface
    , .outbound_data (m_rx_cmd_data )
    , .outbound_last (m_rx_cmd_last )
    , .outbound_valid(m_rx_cmd_valid)
    , .outbound_ready(m_rx_cmd_ready)
);

initial begin : i_setup
    integer         fh;
    reg [(8*8)-1:0] line;
    reg [     23:0] instr;
    bit [     23:0] instr_q [$];
    bit [      4:0] slot;
    bit [      1:0] out_map [3:0];

    // Reset host interface
    m_host_data  = 8'd0;
    m_host_last  = 1'b0;
    m_host_valid = 1'b0;

    // Wait for reset to go high
    while (!rst) @(posedge clk);
    // Wait for reset to go low
    while (rst) @(posedge clk);

    // Load instruction sequence into a queue
    fh = $fopen("instr.hex", "r");
    if (!fh) $fatal(1, "Failed to open instruction hex file");
    while (!$feof(fh)) begin
        if ($fgets(line, fh)) begin
            if ($sscanf(line, "%h", instr)) begin
                $display("Line %03d: 0x%06h", slot, instr);
                instr_q.push_back(instr);
            end
        end
    end
    $fclose(fh);

    // Setup output mapping
    out_map[0] = 2'd3;
    out_map[1] = 2'd0;
    out_map[2] = 2'd2;
    out_map[3] = 2'd1;
    for (slot = 0; slot < 5'd4; slot = (slot + 5'd1)) begin
        $display("%0t: Mapping output %0d -> input %0d", $time, slot, out_map[slot]);
        // Push in the target
        m_host_data  = 8'd0;
        m_host_last  = 1'd0;
        m_host_valid = 1'b1;
        do begin @(posedge clk); end while (!m_rx_cmd_ready);
        // Push in the command
        m_host_data = { CMD_OUT_MAP, 5'd0 };
        do begin @(posedge clk); end while (!m_rx_cmd_ready);
        // Setup output ([1:0]) to input ([3:2]) mapping
        m_host_data = { 4'd0, out_map[slot], slot[1:0] };
        m_host_last = 1'b1;
        do begin @(posedge clk); end while (!m_rx_cmd_ready);
        // Clear the valid
        m_host_last  = 1'b0;
        m_host_valid = 1'b0;
    end

    // Push instruction sequence into the core using commands
    // NOTE: Final instruction load triggers run, so send instructions last
    slot = 5'd0;
    while (instr_q.size() > 0) begin
        $display("%0t: Loading instruction slot %0d", $time, slot);
        // Push in the target
        m_host_data  = 8'd0;
        m_host_last  = 1'd0;
        m_host_valid = 1'b1;
        do begin @(posedge clk); end while (!m_rx_cmd_ready);
        // Push in the command
        m_host_data = {
            (instr_q.size() == 1) ? CMD_LAST_INSTR : CMD_LOAD_INSTR, slot
        };
        do begin @(posedge clk); end while (!m_rx_cmd_ready);
        // Push in the data
        instr       = instr_q.pop_front();
        m_host_data = instr[23:16];
        do begin @(posedge clk); end while (!m_rx_cmd_ready);
        m_host_data = instr[15: 8];
        do begin @(posedge clk); end while (!m_rx_cmd_ready);
        m_host_data = instr[ 7: 0];
        m_host_last = 1'b1;
        do begin @(posedge clk); end while (!m_rx_cmd_ready);
        // Clear the valid
        m_host_last  = 1'b0;
        m_host_valid = 1'b0;
        // Increment slot counter
        slot = (slot + 5'd1);
    end

    // Run for 1000 cycles
    $display("%0t: Running for 1000 cycles", $time);
    repeat (1000) @(posedge clk);
    $display("%0t: Done!", $time);
    $finish;
end

// VCD tracing
initial begin : i_vcd
    string f_name;
    $timeformat(-9, 2, " ns", 20);
    if ($value$plusargs("VCD_FILE=%s", f_name)) begin
        $display("%0t: Capturing VCD file %s", $time, f_name);
        $dumpfile(f_name);
        $dumpvars(0, testbench);
    end else begin
        $display("%0t: No VCD filename provided - disabling VCD capture", $time);
    end
end

endmodule
