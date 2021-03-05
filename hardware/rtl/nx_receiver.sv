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

module nx_receiver #(
      parameter BUS_W     =  8
    , parameter PAYLOAD_W = 24
) (
      input  logic                     clk
    , input  logic                     rst
    // Command interface
    , input  logic [        BUS_W-1:0] cmd_data
    , input  logic                     cmd_last
    , input  logic                     cmd_valid
    , output logic                     cmd_ready
    // Data received
    , output logic [        BUS_W-1:0] rx_command
    , output logic [    PAYLOAD_W-1:0] rx_payload
    , output logic [(PAYLOAD_W/8)-1:0] rx_valid
    , input  logic                     rx_ready
);

endmodule
