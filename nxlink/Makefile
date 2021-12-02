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

# Set default rule
.PHONY: all
all: build

# Source directories
CPP_SRC_DIRS += ./src
CPP_SRC_DIRS += ../common/thirdparty/vcd-writer

# Include directories
CPP_INC_DIRS += $(CPP_SRC_DIRS)
CPP_SRC_DIRS += ../common/work
CPP_INC_DIRS += ../common/thirdparty/cxxopts/include
CPP_INC_DIRS += ../common/thirdparty/concurrentqueue

# Libraries
LIBRARIES +=

LIBS_A  ?= $(patsubst lib%.a,%,$(notdir $(filter lib%.a,$(notdir $(LIBRARIES)))))
LIBS_SO ?= $(patsubst lib%.so,%,$(notdir $(filter lib%.so,$(notdir $(LIBRARIES)))))

# Library directories
LIB_DIRS += $(sort $(dir $(LIBRARIES)))

# Switches
COMPILE_DEBUG ?= no

# Compiler options
CXX_OPTS += $(if $(findstring yes,$(COMPILE_DEBUG)),-g3,-O3)
CXX_OPTS += -fPIC
CXX_OPTS += -std=c++17
CXX_OPTS += $(foreach d,$(CPP_INC_DIRS),-I $(d))
# CXX_OPTS += $(shell python3 -m pybind11 --includes)
CXX_OPTS += -pthread
CXX_OPTS += -MMD -MP
CXX_OPTS += -fpermissive
CXX_OPTS += $(if $(findstring yes,$(COMPILE_DEBUG)),-DNX_EN_DEBUG,)

# Linker options
LD_OPTS += $(CXX_OPTS)
ifneq ($(findstring gcc version 8,$(shell gcc -v 2>&1 | grep 'gcc version')),)
  LD_OPTS += -lstdc++fs
endif
ifneq ($(findstring darwin,$(shell echo $$OSTYPE)),)
  LD_OPTS += -undefined dynamic_lookup
endif
ifneq ($(LIBS_SO),)
  LD_OPTS += --static
  LD_OPTS += $(addprefix -L ,$(LIB_DIRS))
  LD_OPTS += $(addprefix -l,$(LIBS_SO))
endif

# Output
WORK_DIR  ?= work
OBJ_DIR   ?= $(WORK_DIR)/obj
DEPS_DIR  ?= $(WORK_DIR)/deps
EXE_NAME  ?= $(notdir $(abspath .))
EXE_PATH  ?= $(WORK_DIR)/$(EXE_NAME)

MKDIRS += $(WORK_DIR) $(PROTO_DIR) $(OBJ_DIR) $(DEPS_DIR)

# Miscellaneous
QUIET  ?= yes
PREFIX := $(if $(findstring yes,$(QUIET)),@,)

# Build objects
define DO_BUILD_OBJ
# $(1) - Folder path
# $(2) - Extension
$(OBJ_DIR)/%.o: $1/%.$(2) | $(OBJ_DIR) $(DEPS_DIR)
	@echo "# Compiling $$(notdir $$<)"
	$(PREFIX)g++ $(CXX_OPTS) -MT $$@ -MF $(DEPS_DIR)/$$(patsubst %.o,%.d,$$(notdir $$@)) -o $$@ -c $$<

ALL_OBJ += $(patsubst $1/%.$(2),$(OBJ_DIR)/%.o,$(wildcard $1/*.$(2)))
endef
$(foreach d,$(CPP_SRC_DIRS),$(eval $(call DO_BUILD_OBJ,$(d),cpp)))
$(foreach d,$(CPP_SRC_DIRS),$(eval $(call DO_BUILD_OBJ,$(d),cc)))
$(foreach d,$(CPP_SRC_DIRS),$(eval $(call DO_BUILD_OBJ,$(d),c)))

# Include all dependencies
-include $(wildcard $(DEPS_DIR)/*.d)

# Build executable
$(EXE_PATH): $(ALL_OBJ) $(LIBRARIES) | $(WORK_DIR)
	@echo "# Linking objects to form $(notdir $@)"
	$(PREFIX)g++ $(ALL_OBJ) $(LD_OPTS) -o $@

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
	$(PREFIX)sudo make -C ../common/thirdparty/dma_ip_drivers/XDMA/linux-kernel/xdma install -j
	$(PREFIX)chmod +x ../common/thirdparty/dma_ip_drivers/XDMA/linux-kernel/tests/load_driver.sh
	$(PREFIX)cd ../common/thirdparty/dma_ip_drivers/XDMA/linux-kernel/tests && sudo ./load_driver.sh
	$(PREFIX)lspci | grep Xilinx
