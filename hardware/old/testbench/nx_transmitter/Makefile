# Copyright 2021, Peter Birch, mailto:peter@lightlogic.co.uk
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

include ../common/Makefile.inc

# Simulation variables
IV_OUTPUT ?= $(BENCHNAME).vvp

# Arguments to iverilog (compilation)
IV_ARGS += -s$(TB_TOP)
IV_ARGS += -o$(IV_OUTPUT)
IV_ARGS += -g2012
IV_ARGS += $(foreach d,$(SRC_DIRS),-I$(d))
IV_ARGS += $(SRC_FILES)

# Arguments to vvp (runtime)
VVP_ARGS += $(IV_OUTPUT)
ifneq ($(EN_WAVES),no)
  VVP_ARGS += +VCD_FILE=$(SIM_VCD)
endif

$(IV_OUTPUT): $(SRC_FILES) $(HDR_FILES)
	@echo "# Compiling design into $@"
	$(PREFIX)$(IVERILOG) $(IV_ARGS)

.PHONY: build
build: $(IV_OUTPUT)

.PHONY: run
run: build
	@echo "# Simulating design"
	$(PREFIX)$(VVP) $(VVP_ARGS) | tee $(SIM_LOG)

.PHONY: view
view:
	@echo "# Opening waves in GTKWave"
	$(PREFIX)$(GTKWAVE) $(abspath $(SIM_VCD)) $(GTKW_CFG) &

.PHONY: clean
clean:
	@echo "# Cleaning simulation area"
	$(PREFIX)rm -rf $(IV_OUTPUT) $(SIM_LOG) $(SIM_VCD)
