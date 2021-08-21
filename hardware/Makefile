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

# Working directory
WORK_DIR ?= work

# Lint configuration
LINT_TOP ?= nexus
LINT_CFG ?= ./common/lint.cfg
LINT_RPT ?= $(WORK_DIR)/lint.rpt

# SV2V configuration
SV2V_OUT ?= $(WORK_DIR)/nexus.v

# Construct arguments to synthesis
DESIGN_TOP   ?= nexus
SYN_DEFINES  := $(filter-out USE_RAM_MODEL,$(DEFINES))
YOS_TCL_PATH ?= $(WORK_DIR)/yosys.tcl
VVD_TCL_PATH ?= $(WORK_DIR)/vivado.tcl
VVD_TGT_PART ?= xc7a200tfbg484-3

# Construct arguments to Verilator lint
LINT_OPTS += --lint-only
LINT_OPTS += --Wall
LINT_OPTS += $(addprefix -I,$(SRC_DIRS))
LINT_OPTS += $(addprefix -D,$(DEFINES))
LINT_OPTS += $(LINT_CFG)
LINT_OPTS += $(SRC_FILES)
LINT_OPTS += --top $(LINT_TOP)

# Construct arguments to SV2V
SV2V_OPTS += $(addprefix -I,$(SRC_DIRS))
SV2V_OPTS += $(addprefix -D,$(SYN_DEFINES))
SV2V_OPTS += $(SRC_FILES)

# ==============================================================================
# Rules
# ==============================================================================

.PHONY: lint
lint: | $(WORK_DIR)
	@echo "# Running Verilator lint"
	$(PREFIX)verilator $(LINT_OPTS) 2>&1 | tee $(LINT_RPT); exit $${PIPESTATUS[0]}

.PHONY: regress
regress:
	@echo "# Launching regression"
	$(PREFIX)make -C testbench -j$(MAKE_J) run_all

.PHONY: sv2v
sv2v: $(SV2V_OUT)

$(SV2V_OUT): | $(WORK_DIR)
	@echo "# Running SV2V conversion"
	$(PREFIX)sv2v $(SV2V_OPTS) --write $(SV2V_OUT)

.PHONY: syn_yosys
syn_yosys: $(SV2V_OUT) | $(WORK_DIR)
	@echo "# Creating Yosys TCL file"
	$(PREFIX)echo "read -sv $(abspath $<);" > $(YOS_TCL_PATH)
	$(PREFIX)echo "synth_xilinx -top $(DESIGN_TOP) -family xc7;" >> $(YOS_TCL_PATH)
	$(PREFIX)echo "tee -o yosys_$(DESIGN_TOP).rpt stat -tech xilinx;" >> $(YOS_TCL_PATH)
	$(PREFIX)echo "write_verilog yosys_$(DESIGN_TOP).v" >> $(YOS_TCL_PATH)
	@echo "# Running Yosys synthesis"
	$(PREFIX)cd $(WORK_DIR) && yosys -Q -l yosys_$(DESIGN_TOP).log -s $(notdir $(YOS_TCL_PATH))
	@echo "# Extracting total cell count"
	$(PREFIX)awk 'match($$0, /\s+Number of cells:\s+([0-9]+)/, arr) {a=arr[1]} END{print a}' \
	    $(WORK_DIR)/yosys_$(DESIGN_TOP).rpt >> $(WORK_DIR)/yosys_cell_count_$(DESIGN_TOP).txt

.PHONY: syn_vivado
syn_vivado: | $(WORK_DIR)
	@echo "# Creating Vivado TCL file"
	$(PREFIX)echo "read_verilog -sv { $(SRC_FILES) };" > $(VVD_TCL_PATH)
	$(PREFIX)echo "synth_design \
	    -top $(DESIGN_TOP) \
	    -part $(VVD_TGT_PART) \
	    -mode out_of_context \
	    -include_dirs { $(SRC_DIRS) } \
	$(addprefix -verilog_define ,$(SYN_DEFINES));" >> $(VVD_TCL_PATH)
	$(PREFIX)echo "report_utilization -file vivado_$(DESIGN_TOP).rpt" >> $(VVD_TCL_PATH)
	$(PREFIX)echo "write_verilog \
	    -cell $(DESIGN_TOP) \
	    -mode design \
	    -force \
	    vivado_$(DESIGN_TOP).v" >> $(VVD_TCL_PATH)
	@echo "# Running Vivado synthesis"
	$(PREFIX)cd $(WORK_DIR) && vivado -mode batch -source $(notdir $(VVD_TCL_PATH))

.PHONY: clean
clean:
	@echo "# Removing work directory"
	$(PREFIX)rm -rf $(WORK_DIR)
	@echo "# Cleaning all build areas"
	$(PREFIX)make -C testbench -j$(MAKE_J) clean

$(WORK_DIR):
	@echo "# Creating directory $@"
	$(PREFIX)mkdir -p $@
