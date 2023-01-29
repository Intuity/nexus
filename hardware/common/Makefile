# Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
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
# Get the directory of this Makefile
# ==============================================================================
HW_COMMON_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

# ==============================================================================
# Include standard flow components
# ==============================================================================
include $(HW_COMMON_DIR)/../../common/flow/Makefile.vars

# ==============================================================================
# Identify the hardware root directory
# ==============================================================================
HW_ROOT_DIR := $(abspath $(HW_COMMON_DIR)/..)

# ==============================================================================
# RTL input files
# ==============================================================================
SRC_DIRS  += $(HW_COMMON_DIR)/../../common/work
SRC_DIRS  += $(HW_ROOT_DIR)/rtl/primitives
SRC_DIRS  += $(shell find $(HW_ROOT_DIR)/rtl -type d -not -path "*primitives*")
SRC_EXTS  ?= .sv .v
HDR_EXTS  ?= .svh .vh
SRC_FILES ?= $(foreach d,$(SRC_DIRS),$(foreach x,$(SRC_EXTS),$(abspath $(wildcard $(d)/*$(x)))))
HDR_FILES ?= $(foreach d,$(SRC_DIRS),$(foreach x,$(HDR_EXTS),$(abspath $(wildcard $(d)/*$(x)))))

# ==============================================================================
# Defined constants
# ==============================================================================
DEFINES +=

# ==============================================================================
# Options
# ==============================================================================

# Switches
USE_RAM_MODEL ?= yes

# Reactions
DEFINES += $(if $(findstring yes,$(USE_RAM_MODEL)),USE_RAM_MODEL)
