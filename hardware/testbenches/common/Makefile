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

# Get the directory of this Makefile
COMMON_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

# Add testbench as a source directory
SRC_DIRS += ./

# Include hardware common support
include $(COMMON_DIR)/../../common/Makefile

# Design variables
TB_TOP ?= testbench

# Runtime controls
BENCHNAME ?= $(notdir $(abspath .))
SIM_WAVES ?= sim.lxt
SIM_LOG   ?= sim.log
EN_WAVES  ?= no
TRACE_RAM ?= no
EN_TRACE  ?= no

ifeq ($(TRACE_RAM),yes)
  DEFINES += TRACE_RAM
endif

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
  PLUSARGS += +WAVE_FILE=$(SIM_WAVES)
endif

ifneq ($(EN_TRACE),no)
  COMPILE_ARGS += -pfileline=1
endif

# Expand the Python path to include the testbench
PYTHON_PATHS += $(COMMON_DIR)
PYTHON_PATHS += $(abspath .)
PYTHON_PATHS += $(abspath $(COMMON_DIR)/../../..)
PYTHON_PATHS += $(abspath $(COMMON_DIR)/../../../common/python)
PYTHON_PATHS += $(abspath $(COMMON_DIR)/../../../common/work)
PYTHON_PATHS += $(abspath $(COMMON_DIR)/../../../nxmodel/work)
PYTHON_PATHS += $(abspath $(COMMON_DIR)/../../../thirdparty/forastero)
export PYTHONPATH := $(subst $(SPACE),:,$(PYTHON_PATHS)):$(PYTHONPATH)

.PHONY: run results.xml
run: results.xml

.PHONY: view
view:
	$(PREFIX)$(GTKWAVE) $(SIM_WAVES) $(wildcard $(GTKW_CFG)) &

.PHONY: clean
clean::
	$(PREFIX)rm -f *.vcd *.lxt results.xml
