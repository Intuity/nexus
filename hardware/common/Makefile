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

# Force use of bash for evaluation
SHELL := /bin/bash

# Get the directory of this Makefile
HW_COMMON_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

# Identify the hardware root directory
HW_ROOT_DIR := $(abspath $(HW_COMMON_DIR)/..)

# Helpers
SPACE ?=
SPACE := $(SPACE) $(SPACE)

# Input files
SRC_DIRS  += $(HW_ROOT_DIR)/rtl
SRC_EXTS  ?= .sv .v
HDR_EXTS  ?= .svh .vh
SRC_FILES ?= $(foreach d,$(SRC_DIRS),$(foreach x,$(SRC_EXTS),$(abspath $(wildcard $(d)/*$(x)))))
HDR_FILES ?= $(foreach d,$(SRC_DIRS),$(foreach x,$(HDR_EXTS),$(abspath $(wildcard $(d)/*$(x)))))

# Defined constants
DEFINES +=

# Options
MAKE_J        ?= 1
QUIET         ?= yes
USE_RAM_MODEL ?= yes

PREFIX  := $(if $(findstring yes,$(QUIET)),@,)
DEFINES += $(if $(findstring yes,$(USE_RAM_MODEL)),USE_RAM_MODEL)

# Tool paths
IVERILOG  ?= $(shell which iverilog)
VVP       ?= $(shell which vvp)
VERILATOR ?= $(shell which verilator)
GTKWAVE   ?= /Applications/gtkwave.app/Contents/Resources/bin/gtkwave

# Tool specific options
export IVERILOG_DUMPER=lxt
