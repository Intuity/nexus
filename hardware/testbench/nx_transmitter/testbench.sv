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

// Transmit interface
logic [ 7:0] m_tx_target, m_tx_command;
logic [23:0] m_tx_payload;
logic [ 2:0] m_tx_valid;
logic        m_tx_ready;
logic [ 8:0] m_expected [$];
logic [ 8:0] m_captured [$];

initial begin : i_gen_tx
    integer     i;
    logic [7:0] exp, cap;
    // Reset state
    m_tx_target  =  8'd0;
    m_tx_command =  8'd0;
    m_tx_payload = 24'd0;
    m_tx_valid   =  3'd0;
    // Wait for reset to go high
    while (!rst) @(posedge clk);
    // Wait for reset to go low
    while (rst) @(posedge clk);
    // Generate a bunch of random messages
    $display("%0t: Starting to generate stimulus", $time);
    repeat (1000) begin
        // Generate stimulus
        m_tx_target  = $urandom % (1 <<  8);
        m_tx_command = $urandom % (1 <<  8);
        m_tx_payload = $urandom % (1 << 24);
        m_tx_valid   = $urandom & ((1 << 3) - 1);
        // Push into tracking array
        if (m_tx_valid) begin
            m_expected.push_back({ 1'b0, m_tx_target  });
            m_expected.push_back({ 1'b0, m_tx_command });
            for (i = 2; i >= 0; i = (i - 1)) begin
                if (m_tx_valid[i]) begin
                    exp = m_tx_payload >> (i * 8);
                    m_expected.push_back({
                        ((m_tx_valid >> (i+1)) == 0) ? 1'b1 : 1'b0, exp
                    });
                end
            end
        end
        // Log data
        $display(
            "%0t: Transmit - T: 0x%02h, C: 0x%02h, P: 0x%06h, V: 0x%01h",
            $time, m_tx_target, m_tx_command, m_tx_payload, m_tx_valid
        );
        // Wait for transmit to be accepted
        @(posedge clk);
        while (!m_tx_ready) @(posedge clk);
    end
    // Clear the valids
    @(posedge clk);
    m_tx_valid = 3'd0;
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
                1, "Mismatch at %0d between captured 0x%02h and expected 0x%02h",
                i, cap, exp
            );
        end
        i = (i + 1);
    end
    if (m_captured.size() != m_expected.size()) begin
        $fatal(1, "Mismatch between captured and expected lengths");
    end
    // End simulation
    $finish;
end

// Command bus
logic [7:0] m_cmd_data;
logic       m_cmd_last, m_cmd_valid, m_cmd_ready;

initial begin : i_gen_ready
    integer i, delay;
    while (1'b1) begin
        #0;
        m_cmd_ready = $urandom & 1;
        delay       = $urandom % 5;
        repeat (delay+1) @(posedge clk);
    end
end

always @(posedge clk) begin : p_cap_stream
    if (!rst) begin
        if (m_cmd_valid && m_cmd_ready) begin
            // $display("%0t: Received 0x%02h, last %0b", $time, m_cmd_data, m_cmd_last);
            m_captured.push_back({ m_cmd_last, m_cmd_data });
        end
    end
end

// Transmitter instance
nx_transmitter #(
      .TARGET_W ( 8)
    , .BUS_W    ( 8)
    , .PAYLOAD_W(24)
) m_dut (
      .clk(clk)
    , .rst(rst)
    // Data to send
    , .tx_target (m_tx_target )
    , .tx_command(m_tx_command)
    , .tx_payload(m_tx_payload)
    , .tx_valid  (m_tx_valid  )
    , .tx_ready  (m_tx_ready  )
    // Command interface
    , .cmd_data (m_cmd_data )
    , .cmd_last (m_cmd_last )
    , .cmd_valid(m_cmd_valid)
    , .cmd_ready(m_cmd_ready)
);

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
