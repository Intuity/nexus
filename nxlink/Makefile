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

# Source directories
CPP_SRC_DIRS += ./src

# Include directories
CPP_INC_DIRS += $(CPP_SRC_DIRS)
CPP_INC_DIRS += ./thirdparty/cxxopts/include
CPP_INC_DIRS += ./thirdparty/concurrentqueue

# Compiler options
CXX_OPTS += -std=c++14
CXX_OPTS += $(foreach d,$(CPP_INC_DIRS),-I $(d))
CXX_OPTS += -pthread
CXX_OPTS += -g3
CXX_OPTS += -MMD -MP

# Output
WORK_DIR ?= work
OBJ_DIR  ?= $(WORK_DIR)/obj
DEPS_DIR ?= $(WORK_DIR)/deps
EXE_NAME ?= nxlink
EXE_PATH ?= $(WORK_DIR)/$(EXE_NAME)

MKDIRS += $(WORK_DIR) $(OBJ_DIR) $(DEPS_DIR)

# Miscellaneous
QUIET  ?= yes
PREFIX := $(if $(findstring yes,$(QUIET)),@,)

# Build objects
define DO_BUILD_OBJ
$(OBJ_DIR)/%.o: $1/%.cpp | $(OBJ_DIR) $(DEPS_DIR)
	@echo "# Compiling $$(notdir $$<)"
	$(PREFIX)g++ $(CXX_OPTS) -MT $$@ -MF $(DEPS_DIR)/$$(patsubst %.o,%.d,$$(notdir $$@)) -o $$@ -c $$<

ALL_OBJ += $(patsubst $1/%.cpp,$(OBJ_DIR)/%.o,$(wildcard $1/*.cpp))
endef
$(foreach d,$(CPP_SRC_DIRS),$(eval $(call DO_BUILD_OBJ,$(d))))

# Include all dependencies
-include $(wildcard $(DEPS_DIR)/*.d)

# Build executable
$(EXE_PATH): $(ALL_OBJ) | $(WORK_DIR)
	@echo "# Linking objects to form $(notdir $@)"
	$(PREFIX)g++ $(CXX_OPTS) -o $@ $(ALL_OBJ)

.PHONY: build
build: $(EXE_PATH)

# Create directory
$(MKDIRS):
	@echo "# Creating directory $@"
	$(PREFIX)mkdir -p $@

# Clean
.PHONY: clean
clean:
	@echo "# Removing directories"
	$(PREFIX)rm -rf $(MKDIRS)

# Setup DMA IP drivers
.PHONY: setup
setup:
	@echo "# Setting up DMA IP drivers"
	$(PREFIX)sudo make -C thirdparty/dma_ip_drivers/XDMA/linux-kernel/xdma install -j
	$(PREFIX)chmod +x thirdparty/dma_ip_drivers/XDMA/linux-kernel/tests/load_driver.sh
	$(PREFIX)cd thirdparty/dma_ip_drivers/XDMA/linux-kernel/tests && sudo ./load_driver.sh
	$(PREFIX)lspci | grep Xilinx
