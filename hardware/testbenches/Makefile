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

# Default behaviour
.PHONY: all
all: run_all

# Options
IGNORE_FAILURE ?= no

ifeq ($(IGNORE_FAILURE),yes)
  CMD_SUFFIX := || true
endif

# Detect all test areas
SUB_MAKEFILES := $(foreach f,$(wildcard ./*/*/Makefile),$(f))

# Define pre-run rule
.PHONY: __pre_run_generic
__pre_run_generic:
	@echo "# =================================================================="
	@echo "# Preparing to run across $(words $(SUB_MAKEFILES)) units"
	@echo "# =================================================================="
	@echo ""

.PHONY: __pre_run
__pre_run:
	@echo "# =================================================================="
	@echo "# Preparing to run '$(MAKECMDGOALS)' across $(words $(SUB_MAKEFILES)) units"
	@echo "# =================================================================="
	@echo ""

# Setup dispatch per sub-dir
define DO_SUB_DIR
# $(1) - Path to Makefile
.PHONY: __$(subst _,,$(notdir $(patsubst %/,%,$(dir $(1)))))_%
__$(subst _,,$(notdir $(patsubst %/,%,$(dir $(1)))))_%:
	@echo "# Running $$(patsubst __$(subst _,,$(notdir $(patsubst %/,%,$(dir $(1)))))_%,%,$$@) for subfolder $(1)"
	@make -C $(dir $(1)) $$(patsubst __$(subst _,,$(notdir $(patsubst %/,%,$(dir $(1)))))_%,%,$$@) $(CMD_SUFFIX)
.PHONY: __$(notdir $(patsubst %/,%,$(dir $(1))))
__$(notdir $(patsubst %/,%,$(dir $(1)))):
	@echo "# Running subfolder $(notdir $(patsubst %/,%,$(dir $(1))))"
	@make -C $(dir $(1)) $(CMD_SUFFIX)
SUB_GENERIC_TARGETS  += __$(notdir $(patsubst %/,%,$(dir $(1))))
SUB_WILDCARD_TARGETS += __$(subst _,,$(notdir $(patsubst %/,%,$(dir $(1)))))_%
endef
$(foreach t,$(SUB_MAKEFILES),$(eval $(call DO_SUB_DIR,$(t))))

# Empty command
.PHONY: run_all
run_all: $(SUB_GENERIC_TARGETS) | __pre_run_generic
	@echo ""
	@echo "# =================================================================="
	@echo "# Finished running across $(words $(SUB_MAKEFILES)) units"
	@echo "# =================================================================="

# Dispatch any command to all sub-Makefiles
%: $(SUB_WILDCARD_TARGETS) | __pre_run
	@echo ""
	@echo "# =================================================================="
	@echo "# Finished running '$@' across $(words $(SUB_MAKEFILES)) units"
	@echo "# =================================================================="
