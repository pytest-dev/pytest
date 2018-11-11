# Makefile to generate results for performance tests, based on the currently
# checkout Git version.
GIT_DESC:=$(shell git describe --tags --dirty)

all: results/collect-100x10/$(GIT_DESC)

results/collect-%/$(GIT_DESC): fixtures.d/collect-%
	mkdir -p $(dir $@)
	./timeit-shell python -m pytest --collect-only $< | tee $@

# Generate fixture folder for collection tests.
# For collect-100x10 it calls generate_folders with the "target_dir 100 10".
fixtures.d/collect-%:
	@echo "Creating $@" >2
	python collect_stats/generate_folders.py $@ $(subst x, ,$*)
