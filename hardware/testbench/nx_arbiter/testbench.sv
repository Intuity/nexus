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

// Inbound interface A
logic [7:0] m_inbound_a_data;
logic       m_inbound_a_last;
logic       m_inbound_a_valid;
logic       m_inbound_a_ready;

initial begin : i_gen_cmd_a
    integer i, sent;
    // Parts of the command
    logic [ 7:0] target, command;
    logic [23:0] payload;
    logic [ 2:0] pld_valid;
    logic [34:0] exp, cap;
    // Reset state
    m_inbound_a_data  = 8'd0;
    m_inbound_a_last  = 1'b0;
    m_inbound_a_valid = 1'b0;
    // Wait for reset to go high
    while (!rst) @(posedge clk);
    // Wait for reset to go low
    while (rst) @(posedge clk);
    // Generate a bunch of random commands
    $display("%0t: Starting to generate stimulus", $time);
    repeat (10) begin
        // Generate stimulus
        target    = $urandom % (1 <<  8);
        command   = $urandom % (1 <<  8);
        payload   = $urandom % (1 << 24);
        pld_valid = $urandom & ((1 << 3) - 1);
        // Drive onto command bus
        if (pld_valid != 3'd0) begin
            $display(
                "%0t: Transmit - T: %02h, C: %02h, P: %06h, V: %03b",
                $time, target, command, payload, pld_valid
            );
            // Transmit target
            m_inbound_a_data  = target;
            m_inbound_a_last  = 1'b0;
            m_inbound_a_valid = 1'b1;
            do begin @(posedge clk); end while (!m_inbound_a_ready);
            // Transmit command
            m_inbound_a_data  = command;
            exp[31:24]  = command;
            m_inbound_a_valid = 1'b1;
            do begin @(posedge clk); end while (!m_inbound_a_ready);
            // Transmit payload
            for (i = 3; i >= 0; i = (i - 1)) begin
                if (pld_valid[i]) begin
                    pld_valid[i]      = 1'b0;
                    m_inbound_a_data  = (payload >> (i * 8));
                    m_inbound_a_last  = ~(|pld_valid);
                    m_inbound_a_valid = 1'b1;
                    do begin @(posedge clk); end while (!m_inbound_a_ready);
                end
            end
        // Skip transmit, wait one clock cycle
        end else begin
            @(posedge clk);
        end
    end
    // Clear the valids
    @(posedge clk);
    m_inbound_a_valid = 3'd0;
    // Allow some time to drain
    repeat (30) @(posedge clk);
    // Finish the simulation
    $finish;
end

// Inbound interface B
logic [7:0] m_inbound_b_data;
logic       m_inbound_b_last;
logic       m_inbound_b_valid;
logic       m_inbound_b_ready;

initial begin : i_gen_cmd_b
    integer i, sent;
    // Parts of the command
    logic [ 7:0] target, command;
    logic [23:0] payload;
    logic [ 2:0] pld_valid;
    logic [34:0] exp, cap;
    // Reset state
    m_inbound_b_data  = 8'd0;
    m_inbound_b_last  = 1'b0;
    m_inbound_b_valid = 1'b0;
    // Wait for reset to go high
    while (!rst) @(posedge clk);
    // Wait for reset to go low
    while (rst) @(posedge clk);
    // Generate a bunch of random commands
    $display("%0t: Starting to generate stimulus", $time);
    repeat (10) begin
        // Generate stimulus
        target    = $urandom % (1 <<  8);
        command   = $urandom % (1 <<  8);
        payload   = $urandom % (1 << 24);
        pld_valid = $urandom & ((1 << 3) - 1);
        // Drive onto command bus
        if (pld_valid != 3'd0) begin
            $display(
                "%0t: Transmit - T: %02h, C: %02h, P: %06h, V: %03b",
                $time, target, command, payload, pld_valid
            );
            // Transmit target
            m_inbound_b_data  = target;
            m_inbound_b_last  = 1'b0;
            m_inbound_b_valid = 1'b1;
            do begin @(posedge clk); end while (!m_inbound_b_ready);
            // Transmit command
            m_inbound_b_data  = command;
            exp[31:24]  = command;
            m_inbound_b_valid = 1'b1;
            do begin @(posedge clk); end while (!m_inbound_b_ready);
            // Transmit payload
            for (i = 3; i >= 0; i = (i - 1)) begin
                if (pld_valid[i]) begin
                    pld_valid[i]      = 1'b0;
                    m_inbound_b_data  = (payload >> (i * 8));
                    m_inbound_b_last  = ~(|pld_valid);
                    m_inbound_b_valid = 1'b1;
                    do begin @(posedge clk); end while (!m_inbound_b_ready);
                end
            end
        // Skip transmit, wait one clock cycle
        end else begin
            @(posedge clk);
        end
    end
    // Clear the valids
    @(posedge clk);
    m_inbound_b_valid = 3'd0;
    // Allow some time to drain
    repeat (30) @(posedge clk);
    // Finish the simulation
    $finish;
end

// Outbound interface
logic [7:0] m_outbound_data;
logic       m_outbound_last;
logic       m_outbound_valid;
logic       m_outbound_ready;

assign m_outbound_ready = 1'b1;

// Arbiter instance
nx_arbiter #(
    .BUS_W(8)
) m_dut (
      .clk(clk)
    , .rst(rst)
    // Inbound interface A
    , .inbound_a_data (m_inbound_a_data )
    , .inbound_a_last (m_inbound_a_last )
    , .inbound_a_valid(m_inbound_a_valid)
    , .inbound_a_ready(m_inbound_a_ready)
    // Inbound interface B
    , .inbound_b_data (m_inbound_b_data )
    , .inbound_b_last (m_inbound_b_last )
    , .inbound_b_valid(m_inbound_b_valid)
    , .inbound_b_ready(m_inbound_b_ready)
    // Outbound interface
    , .outbound_data (m_outbound_data )
    , .outbound_last (m_outbound_last )
    , .outbound_valid(m_outbound_valid)
    , .outbound_ready(m_outbound_ready)
);

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
