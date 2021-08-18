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

LINT_TOP ?= nexus
LINT_CFG ?= ./common/lint.cfg
LINT_RPT ?=

# Construct arguments to Verilator lint
LINT_OPTS += --lint-only
LINT_OPTS += --Wall
LINT_OPTS += $(addprefix -I,$(SRC_DIRS))
LINT_OPTS += $(addprefix -D,$(DEFINES))
LINT_OPTS += $(LINT_CFG)
LINT_OPTS += $(SRC_FILES)
LINT_OPTS += --top $(LINT_TOP)

LINT_SFX ?= $(if $(LINT_RPT),2>&1 | tee $(LINT_RPT))

# ==============================================================================
# Rules
# ==============================================================================

.PHONY: lint
lint:
	@echo "# Running Verilator lint"
	$(PREFIX)verilator $(LINT_OPTS) $(LINT_SFX)

.PHONY: regress
regress:
	@echo "# Launching regression"
	$(PREFIX)make -C testbench -j$(MAKE_J) run_all

.PHONY: clean
clean:
	@echo "# Cleaning all build areas"
	$(PREFIX)make -C testbench -j$(MAKE_J) clean
