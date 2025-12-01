#!/usr/bin/env bash

##############################################################################
# Makefile: Build System for C++ Components
#
# Purpose:
# Compile all C++ boundary testing and fuzzing components with proper
# optimization and error checking.
#
# Usage:
#   make              # Build all components
#   make clean        # Remove build artifacts
#   make test         # Build and run quick validation
##############################################################################

CXX := g++
CXXFLAGS := -std=c++17 -O2 -Wall -Wextra -Wpedantic
BUILD_DIR := build
TARGETS := boundary_tester fuzzer

.PHONY: all clean test

all: $(BUILD_DIR) $(addprefix $(BUILD_DIR)/, $(TARGETS))

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/boundary_tester: boundary_tester.cpp
	$(CXX) $(CXXFLAGS) $< -o $@

$(BUILD_DIR)/fuzzer: fuzzer.cpp
	$(CXX) $(CXXFLAGS) $< -o $@

test: all
	@echo "Running quick validation tests..."
	@$(BUILD_DIR)/boundary_tester int_overflow
	@$(BUILD_DIR)/fuzzer extreme_numbers 5

clean:
	rm -rf $(BUILD_DIR)
