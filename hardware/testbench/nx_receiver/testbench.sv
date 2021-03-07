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

// Command bus
logic [ 7:0] m_cmd_data;
logic        m_cmd_last, m_cmd_valid, m_cmd_ready;
logic [34:0] m_expected [$];
logic [34:0] m_captured [$];

initial begin : i_gen_cmd
    integer i, sent;
    // Parts of the command
    logic [ 7:0] target, command;
    logic [23:0] payload;
    logic [ 2:0] pld_valid;
    logic [34:0] exp, cap;
    // Reset state
    m_cmd_data  = 8'd0;
    m_cmd_last  = 1'b0;
    m_cmd_valid = 1'b0;
    // Wait for reset to go high
    while (!rst) @(posedge clk);
    // Wait for reset to go low
    while (rst) @(posedge clk);
    // Generate a bunch of random commands
    $display("%0t: Starting to generate stimulus", $time);
    repeat (1000) begin
        // Clear entry
        exp       = 35'd0;
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
            m_cmd_data  = target;
            m_cmd_last  = 1'b0;
            m_cmd_valid = 1'b1;
            do begin @(posedge clk); end while (!m_cmd_ready);
            // Transmit command
            m_cmd_data  = command;
            exp[31:24]  = command;
            m_cmd_valid = 1'b1;
            do begin @(posedge clk); end while (!m_cmd_ready);
            // Update the expected data
            sent = 0;
            for (i = 0; i < 3; i = (i + 1)) begin
                if (pld_valid[i]) begin
                    if (sent == 0) begin
                        exp[ 7: 0] = (payload >> (i * 8));
                        exp[   32] = 1'b1;
                    end
                    else if (sent == 1) begin
                        exp[15: 8] = (payload >> (i * 8));
                        exp[   33] = 1'b1;
                    end
                    else if (sent == 2) begin
                        exp[23:16] = (payload >> (i * 8));
                        exp[   34] = 1'b1;
                    end
                    sent = (sent + 1);
                end
            end
            // Transmit payload
            for (i = 3; i >= 0; i = (i - 1)) begin
                if (pld_valid[i]) begin
                    pld_valid[i] = 1'b0;
                    m_cmd_data   = (payload >> (i * 8));
                    m_cmd_last   = ~(|pld_valid);
                    m_cmd_valid  = 1'b1;
                    do begin @(posedge clk); end while (!m_cmd_ready);
                end
            end
            // Record entry
            m_expected.push_back(exp);
        // Skip transmit, wait one clock cycle
        end else begin
            @(posedge clk);
        end
    end
    // Clear the valids
    @(posedge clk);
    m_cmd_valid = 3'd0;
    // Allow some time to drain
    repeat (30) @(posedge clk);
    // Cross check expectation against capture
    $display(
        "%0t: Captured %0d, expected %0d",
        $time, m_captured.size(), m_expected.size()
    );
    i = 0;
    while (m_captured.size() > 0) begin
        cap = m_captured.pop_front();
        exp = m_expected.pop_front();
        if (cap != exp) begin
            $fatal(
                1, "Mismatch at %0d between captured 0x%010h and expected 0x%010h",
                i, cap, exp
            );
        end
        i = (i + 1);
    end
    if (m_captured.size() != m_expected.size()) begin
        $fatal(1, "Mismatch between captured and expected lengths");
    end
    // Finish the simulation
    $finish;
end

// Receive interface
logic [ 7:0] m_rx_command;
logic [23:0] m_rx_payload;
logic [ 2:0] m_rx_valid;
logic        m_rx_complete;
logic        m_rx_ready;

initial begin : i_gen_ready
    integer i, delay;
    while (1'b1) begin
        #0;
        m_rx_ready = $urandom & 1;
        delay      = $urandom % 5;
        repeat (delay+1) @(posedge clk);
    end
end

always @(posedge clk) begin : p_cap_rx
    if (!rst) begin
        if (m_rx_complete && m_rx_ready) begin
            // $display(
            //     "%0t: Captured C: 0x%02h P: 0x%06h V: %03b",
            //     $time, m_rx_command, m_rx_payload, m_rx_valid
            // );
            m_captured.push_back({
                m_rx_valid, m_rx_command, m_rx_payload
            });
        end
    end
end

// Receiver instance
nx_receiver #(
      .TARGET_W ( 8)
    , .BUS_W    ( 8)
    , .PAYLOAD_W(24)
) m_dut (
      .clk(clk)
    , .rst(rst)
    // Command interface
    , .cmd_data (m_cmd_data )
    , .cmd_last (m_cmd_last )
    , .cmd_valid(m_cmd_valid)
    , .cmd_ready(m_cmd_ready)
    // Data received
    , .rx_command (m_rx_command )
    , .rx_payload (m_rx_payload )
    , .rx_valid   (m_rx_valid   )
    , .rx_complete(m_rx_complete)
    , .rx_ready   (m_rx_ready   )
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
