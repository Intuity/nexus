# Detect all test areas
TESTS := $(foreach f,$(wildcard ./*/Makefile),$(notdir $(patsubst %/,%,$(dir $(f)))))

# Define pre-run rule
.PHONY: __pre_run
__pre_run:
	@echo "# =================================================================="
	@echo "# Preparing to run '$(MAKECMDGOALS)' across $(words $(TESTS)) tests"
	@echo "# =================================================================="
	@echo ""

# Setup dispatch per sub-dir
define DO_SUB_DIR
# $(1) - Test directory name
.PHONY: $(1)_% | __pre_run
$(1)_%:
	@echo "# Running $$@ for test $(1)"
	@make -C $(1) $$(patsubst $(1)_%,%,$$@)
TEST_TARGETS += $(1)_%
endef
$(foreach t,$(TESTS),$(eval $(call DO_SUB_DIR,$(t))))

# Dispatch any command to all tests
%: $(TEST_TARGETS) | __pre_run
	@echo ""
	@echo "# =================================================================="
	@echo "# Finished running '$@' across $(words $(TESTS)) tests"
	@echo "# =================================================================="
