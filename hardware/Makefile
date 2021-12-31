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

include ./common/Makefile

# ==============================================================================
# Options
# ==============================================================================

# Common attributes
DESIGN_TOP ?= nexus

# Lint configuration
LINT_CFG ?= ./common/lint.cfg
LINT_RPT ?= $(WORKING_DIR)/lint.rpt

# Construct arguments to synthesis
SYN_DEFINES  := $(filter-out USE_RAM_MODEL,$(DEFINES))
YOS_TCL_PATH ?= $(WORKING_DIR)/yosys.tcl
VVD_TCL_PATH ?= $(WORKING_DIR)/vivado.tcl
VVD_TGT_PART ?= xc7a200tfbg484-3

# Construct arguments to Verilator lint
LINT_OPTS += --lint-only
LINT_OPTS += --Wall
LINT_OPTS += $(addprefix -I,$(SRC_DIRS))
LINT_OPTS += $(addprefix -D,$(DEFINES))
LINT_OPTS += $(LINT_CFG)
LINT_OPTS += $(filter-out $(abspath rtl/fpga/nx_artix_200t.v),$(SRC_FILES))
LINT_OPTS += --top $(DESIGN_TOP)

$(info SRC_FILES=$(SRC_FILES))

# Construct arguments to SV2V
SV2V_OUT  ?= $(WORKING_DIR)/$(DESIGN_TOP).v
SV2V_OPTS += $(addprefix -I,$(SRC_DIRS))
SV2V_OPTS += $(addprefix -D,$(SYN_DEFINES))
SV2V_OPTS += $(SRC_FILES)

# ==============================================================================
# Rules
# ==============================================================================

.PHONY: lint
lint: | $(WORKING_DIR)
	@echo "# Running Verilator lint"
	$(PREFIX)verilator $(LINT_OPTS) 2>&1 | tee $(LINT_RPT); exit $${PIPESTATUS[0]}

.PHONY: regress
regress:
	@echo "# Launching regression"
	$(PREFIX)make -C testbenches -j$(MAKE_J) run_all

.PHONY: sv2v
sv2v: $(SV2V_OUT)

$(SV2V_OUT): | $(WORKING_DIR)
	@echo "# Running SV2V conversion"
	$(PREFIX)sv2v $(SV2V_OPTS) --write $(SV2V_OUT)

.PHONY: syn_yosys
syn_yosys: $(SV2V_OUT) | $(WORKING_DIR)
	@echo "# Creating Yosys TCL file"
	$(PREFIX)echo "read -sv $(abspath $<);" > $(YOS_TCL_PATH)
	$(PREFIX)echo "synth_xilinx -top $(DESIGN_TOP) -family xc7;" >> $(YOS_TCL_PATH)
	$(PREFIX)echo "tee -o yosys_$(DESIGN_TOP).rpt stat -tech xilinx;" >> $(YOS_TCL_PATH)
	$(PREFIX)echo "write_verilog yosys_$(DESIGN_TOP).v" >> $(YOS_TCL_PATH)
	@echo "# Running Yosys synthesis"
	$(PREFIX)cd $(WORKING_DIR) && yosys -Q -l yosys_$(DESIGN_TOP).log -s $(notdir $(YOS_TCL_PATH))
	@echo "# Extracting total cell counts"
	$(PREFIX)python3 common/parse_yosys_rpt.py $(WORKING_DIR)/yosys_$(DESIGN_TOP).rpt \
	    $(WORKING_DIR)/yosys_$(DESIGN_TOP).csv

include common/Makefile.vivado

# ==============================================================================
# Standard Rules
# ==============================================================================

clean::
	@echo "# Cleaning all build areas"
	$(PREFIX)make -C testbench -j$(MAKE_J) clean

include ../common/flow/Makefile.rules
