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

# Third-party libraries
ROOT_CXXOPTS          ?= ./thirdparty/cxxopts
ROOT_CONCURRENT_QUEUE ?= ./thirdparty/concurrentqueue
ROOT_GRPC             ?= ./thirdparty/grpc

# Required tools
PROTOC      ?= $(ROOT_GRPC)/third_party/protobuf/src/protoc
GRPC_PLUGIN ?= $(ROOT_GRPC)/cmake/build/grpc_cpp_plugin

# Source directories
# - Protobuf
PROTO_SRC_DIRS += ./rpc
# - C++
CPP_SRC_DIRS   += ./src
CPP_SRC_DIRS   += ./work/proto
CPP_SRC_DIRS   += $(ROOT_GRPC)/third_party/address_sorting

# Protobuf sources
PROTO_SRCS += $(foreach d,$(PROTO_SRC_DIRS),$(wildcard $(d)/*.proto))

# Include directories
# - Protobuf
PROTO_INC_DIRS += $(PROTO_SRC_DIRS)
PROTO_INC_DIRS += $(ROOT_GRPC)/third_party/protobuf/src
# - C++
CPP_INC_DIRS   += $(CPP_SRC_DIRS)
CPP_INC_DIRS   += $(ROOT_CXXOPTS)/include
CPP_INC_DIRS   += $(ROOT_CONCURRENT_QUEUE)
CPP_INC_DIRS   += $(ROOT_GRPC)/include
CPP_INC_DIRS   += $(ROOT_GRPC)/third_party/protobuf/src
CPP_INC_DIRS   += $(ROOT_GRPC)/third_party/abseil-cpp
CPP_INC_DIRS   += $(ROOT_GRPC)/third_party/address_sorting/include

# Libraries
LIB_GRPC     ?= $(wildcard $(ROOT_GRPC)/cmake/build/*.a)
LIB_PROTOBUF ?= $(ROOT_GRPC)/third_party/protobuf/src/.libs/libprotobuf.a
LIB_ABSEIL   ?= $(wildcard $(ROOT_GRPC)/third_party/abseil-cpp/absl/*/libabsl*.a)
LIB_CARES    ?= $(ROOT_GRPC)/third_party/cares/cares/.libs/libcares.a

LIBRARIES += $(LIB_PROTOBUF)
LIBRARIES += $(LIB_GRPC)
LIBRARIES += $(LIB_ABSEIL)
LIBRARIES += $(LIB_CARES)

LIBS_A  ?= $(patsubst lib%.a,%,$(notdir $(filter lib%.a,$(notdir $(LIBRARIES)))))
LIBS_SO ?= $(patsubst lib%.so,%,$(notdir $(filter lib%.so,$(notdir $(LIBRARIES)))))

# Library directories
LIB_DIRS += $(sort $(dir $(LIBRARIES)))

# Compiler options
CXX_OPTS += -std=c++14
CXX_OPTS += $(foreach d,$(CPP_INC_DIRS),-I $(d))
CXX_OPTS += -pthread
CXX_OPTS += -g3
CXX_OPTS += -MMD -MP
CXX_OPTS += -fpermissive

# Linker options
LD_OPTS += $(CXX_OPTS)
LD_OPTS += --static
LD_OPTS += $(addprefix -L ,$(LIB_DIRS))
LD_OPTS += $(addprefix -l,$(filter-out absl_debugging_internal absl_demangle_internal,$(LIBS_A)))
LD_OPTS += $(addprefix -l,$(LIBS_SO))
LD_OPTS += -labsl_debugging_internal
LD_OPTS += -labsl_demangle_internal
LD_OPTS += -lz

# Output
WORK_DIR  ?= work
PROTO_DIR ?= $(WORK_DIR)/proto
OBJ_DIR   ?= $(WORK_DIR)/obj
DEPS_DIR  ?= $(WORK_DIR)/deps
EXE_NAME  ?= nxlink
EXE_PATH  ?= $(WORK_DIR)/$(EXE_NAME)

MKDIRS += $(WORK_DIR) $(PROTO_DIR) $(OBJ_DIR) $(DEPS_DIR)

# Miscellaneous
QUIET  ?= yes
PREFIX := $(if $(findstring yes,$(QUIET)),@,)

# Build protobuf declarations
$(PROTO_DIR)/proto.d: $(PROTO_SRCS) | $(PROTO_DIR)
	@echo "# Generating code from protobuf"
	$(PREFIX)$(PROTOC) $(foreach d,$(PROTO_INC_DIRS),--proto_path=$(d)) \
	 --cpp_out=$(PROTO_DIR) \
	 $(PROTO_SRCS)
	$(PREFIX)$(PROTOC) $(foreach d,$(PROTO_INC_DIRS),--proto_path=$(d)) \
	 --grpc_out=$(PROTO_DIR) \
	 --plugin=protoc-gen-grpc=$(GRPC_PLUGIN) \
	 $(PROTO_SRCS)
	$(PREFIX)touch $@

# Build objects
define DO_BUILD_OBJ
# $(1) - Folder path
# $(2) - Extension
$(OBJ_DIR)/%.o: $1/%.$(2) $(PROTO_DIR)/proto.d | $(OBJ_DIR) $(DEPS_DIR)
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
	$(PREFIX)sudo make -C thirdparty/dma_ip_drivers/XDMA/linux-kernel/xdma install -j
	$(PREFIX)chmod +x thirdparty/dma_ip_drivers/XDMA/linux-kernel/tests/load_driver.sh
	$(PREFIX)cd thirdparty/dma_ip_drivers/XDMA/linux-kernel/tests && sudo ./load_driver.sh
	$(PREFIX)lspci | grep Xilinx

# Build gRPC library if not available
$(LIB_GRPC):
	@echo "# Building gRPC from source"
	@cd $(ROOT_GRPC) && mkdir -p cmake/build && cd cmake/build && \
	 cmake && make -j4

# Build the Protocol Buffers protoc tool if not available
$(PROTOC):
	@echo "# Building protoc from source"
	@cd $(ROOT_GRPC)/third_party/protobuf/ && ./autogen.sh && ./configure && \
	 make -j4

# Build Abseil library if not available
$(LIB_ABSEIL):
	@echo "# Building Abseil from source"
	@cd $(ROOT_GRPC)/third_party/abseil-cpp && \
	 cmake -DCMAKE_CXX_STANDARD=11 && cmake --build . --target all

# Build c-ares library if not available
$(LIB_CARES):
	@echo "# Building c-ares from source"
	@cd $(ROOT_GRPC)/third_party/cares/cares && ./buildconf && ./configure && \
	 make
