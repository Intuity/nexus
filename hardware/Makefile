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
RTL_SRC_DIRS ?= $(WORK_DIR)
RTL_SRCS     ?= $(SV2V_OUT)
SYN_FULL     ?= yes

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
SV2V_OPTS += $(addprefix -D,$(filter-out USE_RAM_MODEL,$(DEFINES)))
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

include ../tests/common/Makefile.synth
synth: $(SV2V_OUT)

.PHONY: clean
clean:
	@echo "# Removing work directory"
	$(PREFIX)rm -rf $(WORK_DIR)
	@echo "# Cleaning all build areas"
	$(PREFIX)make -C testbench -j$(MAKE_J) clean

$(WORK_DIR):
	@echo "# Creating directory $@"
	$(PREFIX)mkdir -p $@
