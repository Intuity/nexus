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

# Get the directory of this Makefile
COMMON_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

# Helpers
SPACE ?=
SPACE := $(SPACE) $(SPACE)

# Input files
SRC_DIRS  ?= ../../rtl ./
SRC_EXTS  ?= .sv .v
HDR_EXTS  ?= .svh .vh
SRC_FILES ?= $(foreach d,$(SRC_DIRS),$(foreach x,$(SRC_EXTS),$(abspath $(wildcard $(d)/*$(x)))))
HDR_FILES ?= $(foreach d,$(SRC_DIRS),$(foreach x,$(HDR_EXTS),$(abspath $(wildcard $(d)/*$(x)))))

# Defined constants
DEFINES +=

# Design variables
TB_TOP ?= testbench

# Runtime controls
BENCHNAME ?= $(notdir $(abspath .))
QUIET     ?= yes
SIM_VCD   ?= sim.vcd
SIM_LOG   ?= sim.log
EN_WAVES  ?= no

ifeq ($(QUIET),yes)
  PREFIX := @
else
  PREFIX :=
endif

# Tool paths
IVERILOG ?= $(shell which iverilog)
VVP      ?= $(shell which vvp)
GTKWAVE  ?= /Applications/gtkwave.app/Contents/Resources/bin/gtkwave

# Wave viewer variables
GTKW_CFG ?= $(wildcard $(BENCHNAME).gtkw)

# CocoTB setup
SIM             ?= icarus
DEFINES         += sim_$(SIM)
TOPLEVEL_LANG   ?= verilog
VERILOG_SOURCES += $(SRC_FILES) ./wrapper/testbench.sv
TOPLEVEL        ?= testbench
MODULE          ?= entrypoint
COMPILE_ARGS    += $(addprefix -I ,$(abspath $(SRC_DIRS)))
COMPILE_ARGS    += $(addprefix -D ,$(DEFINES))

ifneq ($(EN_WAVES),no)
  PLUSARGS += +VCD_FILE=$(SIM_VCD)
endif

# Expand the Python path to include the testbench
PYTHON_PATHS += $(COMMON_DIR)
PYTHON_PATHS += $(abspath .)
export PYTHONPATH := $(subst $(SPACE),:,$(PYTHON_PATHS)):$(PYTHONPATH)

.PHONY: run results.xml
run: results.xml

.PHONY: view
view:
	$(PREFIX)$(GTKWAVE) $(SIM_VCD) $(GTKW_CFG) &
