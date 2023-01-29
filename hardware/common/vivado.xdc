# Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Setup a 200 MHz clock
create_clock -period 5.000 -name clk -waveform { 0.000 2.500 } [get_ports clk_i]
# Define the clock source structure
set_property HD.CLK_SRC BUFGCTRL_X0Y15 [get_ports clk_i]
# Setup a custom clock jitter
set_system_jitter 0.0
set_clock_latency -source -min 0.10
set_clock_latency -source -max 0.20
# Set I/O delays
set_input_delay -clock clk -max 0.500 [
    get_ports * -filter {DIRECTION == IN && NAME !~ "*clk*" && NAME !~ "*rst*"}
]
set_output_delay -clock clk -max 0.500 [
    get_ports * -filter {DIRECTION == OUT && NAME !~ "*clk*" && NAME !~ "*rst*"}
]
