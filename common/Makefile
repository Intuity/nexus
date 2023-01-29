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

# ==============================================================================
# Include common variables
# ==============================================================================

include flow/Makefile.vars

# ==============================================================================
# Variables
# ==============================================================================

# Find all Packtype specifications
PACKTYPE_SPEC_DIR ?= constants
PACKTYPE_SPECS    += $(sort $(wildcard $(PACKTYPE_SPEC_DIR)/*.py))

# Specify types to render
PACKTYPE_RENDER += sv
PACKTYPE_RENDER += py
PACKTYPE_RENDER += cpp
PACKTYPE_RENDER += html

# Accumulate options
PACKTYPE_OPTS += $(addprefix --render ,$(PACKTYPE_RENDER))
PACKTYPE_OPTS += $(if $(findstring yes,$(DEBUG)),--debug,)

# Extend path
export PYTHONPATH := $(PYTHONPATH):$(abspath python)

# ==============================================================================
# Rules
# ==============================================================================

$(WORKING_DIR)/%.d: $(PACKTYPE_SPEC_DIR)/%.py | $(WORKING_DIR)
	@echo "# Generating definitions from $<"
	$(PACKTYPE) $< $(WORKING_DIR) $(PACKTYPE_OPTS)
	$(PREFIX)touch $@

$(WORKING_DIR)/nxisa.hpp: $(wildcard python/nxisa/*.py) | $(WORKING_DIR)
	@echo "# Generating NXISA C++ definitions"
	$(PREFIX)python3 -m nxisa.export_cpp $@

$(WORKING_DIR)/NXISA.sv: $(wildcard python/nxisa/*.py) | $(WORKING_DIR)
	@echo "# Generating NXISA SV definitions"
	$(PREFIX)python3 -m nxisa.export_sv $@

.PHONY: generate
generate: $(addprefix $(WORKING_DIR)/,$(patsubst %.py,%.d,$(notdir $(PACKTYPE_SPECS)))) $(WORKING_DIR)/nxisa.hpp $(WORKING_DIR)/NXISA.sv

.PHONY: setup_surelog
setup_surelog:
	@echo "# Compiling surelog"
	@make -C thirdparty/surelog PREFIX=$(abspath thirdparty/surelog)/install
	@make -C thirdparty/surelog install PREFIX=$(abspath thirdparty/surelog)/install

.PHONY: setup_slang
setup_slang:
	@echo "# Compiling slang"
	@mkdir -p thirdparty/slang/build
	@cd thirdparty/slang/build && \
	    cmake \
	    -DCMAKE_CXX_COMPILER=clang++ \
	    -DCMAKE_BUILD_TYPE=Release \
	    -DCMAKE_INSTALL_PREFIX=$(abspath thirdparty/slang)/install \
	    -DSLANG_INCLUDE_TESTS=OFF \
	    ..
	@cd thirdparty/slang/build && make -j6
	@cd thirdparty/slang/build && make install

.PHONY: setup
setup: setup_surelog setup_slang

# ==============================================================================
# Include common rules
# ==============================================================================

include flow/Makefile.rules
