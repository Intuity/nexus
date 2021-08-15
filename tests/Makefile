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

# Detect all test areas
SUB_MAKEFILES := $(foreach f,$(wildcard ./*/Makefile),$(notdir $(patsubst %/,%,$(dir $(f)))))

# Define pre-run rule
.PHONY: __pre_run
__pre_run:
	@echo "# =================================================================="
	@echo "# Preparing to run '$(MAKECMDGOALS)' across $(words $(SUB_MAKEFILES)) units"
	@echo "# =================================================================="
	@echo ""

# Setup dispatch per sub-dir
define DO_SUB_DIR
# $(1) - Test directory name
.PHONY: $(subst _,,$(1))_% | __pre_run
$(subst _,,$(1))_%:
	@echo "# Running $$@ for test $(subst _,,$(1))"
	@make -C $(1) $$(patsubst $(subst _,,$(1))_%,%,$$@)
SUB_TARGETS += $(subst _,,$(1))_%
endef
$(foreach t,$(SUB_MAKEFILES),$(eval $(call DO_SUB_DIR,$(t))))

# Dispatch any command to all sub-Makefiles
%: $(SUB_TARGETS) | __pre_run
	@echo ""
	@echo "# =================================================================="
	@echo "# Finished running '$@' across $(words $(SUB_MAKEFILES)) units"
	@echo "# =================================================================="
