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

# Include directories
CPP_INC_DIRS += $(CPP_SRC_DIRS)
CPP_SRC_DIRS += ../common/work
CPP_INC_DIRS += ../common/thirdparty/cxxopts/include
CPP_INC_DIRS += ../common/thirdparty/json/single_include/nlohmann
CPP_INC_DIRS += ../common/thirdparty/surelog/install/include
CPP_INC_DIRS += ../common/thirdparty/surelog/install/include/surelog

# Libraries
LIBRARIES += ../common/thirdparty/surelog/install/lib/surelog/libflatbuffers.a
LIBRARIES += ../common/thirdparty/surelog/install/lib/surelog/libantlr4-runtime.a
LIBRARIES += ../common/thirdparty/surelog/install/lib/surelog/libsurelog.a
LIBRARIES += ../common/thirdparty/surelog/install/lib/uhdm/libkj.a
LIBRARIES += ../common/thirdparty/surelog/install/lib/uhdm/libcapnp.a
LIBRARIES += ../common/thirdparty/surelog/install/lib/uhdm/libuhdm.a

LIBS_A  ?= $(patsubst lib%.a,%,$(notdir $(filter lib%.a,$(notdir $(LIBRARIES)))))
LIBS_SO ?= $(patsubst lib%.so,%,$(notdir $(filter lib%.so,$(notdir $(LIBRARIES)))))

# Library directories
LIB_DIRS += $(sort $(dir $(abspath $(LIBRARIES))))

# Switches
COMPILE_DEBUG ?= no

# Compiler options
CXX_OPTS += $(if $(findstring yes,$(COMPILE_DEBUG)),-g3,-O3)
CXX_OPTS += -fPIC
CXX_OPTS += -std=c++17
CXX_OPTS += $(foreach d,$(abspath $(CPP_INC_DIRS)),-I $(d))
CXX_OPTS += $(shell python3 -m pybind11 --includes)
CXX_OPTS += -pthread
CXX_OPTS += -MMD -MP
CXX_OPTS += -fpermissive
ifneq ($(findstring darwin,$(shell echo $$OSTYPE)),)
  CXX_OPTS += -mmacosx-version-min=$(shell sw_vers -productVersion | cut -d '.' -f-2)
endif

# Linker options
LD_OPTS += $(CXX_OPTS)
ifneq ($(findstring gcc version 8,$(shell gcc -v 2>&1 | grep 'gcc version')),)
  LD_OPTS += -lstdc++fs
endif
ifneq ($(findstring darwin,$(shell echo $$OSTYPE)),)
  LD_OPTS += -undefined dynamic_lookup
endif
ifneq ($(LIBS_A),)
  LD_OPTS += $(addprefix -L ,$(LIB_DIRS))
  LD_OPTS += $(addprefix -l,$(LIBS_A))
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
LIB_PATH  ?= $(WORK_DIR)/$(EXE_NAME)$(shell python3-config --extension-suffix)

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
	$(PREFIX)g++ $(filter-out $(wildcard work/obj/*py.o),$(ALL_OBJ)) $(LD_OPTS) -o $@

# Build library
$(LIB_PATH): $(ALL_OBJ) $(LIBRARIES) | $(WORK_DIR)
	@echo "# Linking objects to form $(notdir $@)"
	$(PREFIX)g++ -shared $(filter-out work/obj/main.o,$(ALL_OBJ)) $(LD_OPTS) -o $@

.PHONY: build
build: $(EXE_PATH) $(LIB_PATH)

# Create directory
$(MKDIRS):
	@echo "# Creating directory $@"
	$(PREFIX)mkdir -p $@

# Clean
.PHONY: clean
clean:
	@echo "# Removing directories"
	$(PREFIX)rm -rf $(MKDIRS)
