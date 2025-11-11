# Container Playground Guide

The repository bundles a handful of experimental Docker configurations that try to exercise pytest's dependency graph under intentionally awkward conditions.

## Prerequisites

* A working Docker Engine installation (the standard `docker` CLI must be available in your shell).
* Enough disk space to build multiple images – several of the variants deliberately install heavy dependency sets.

## Running tests for a specific variant

To build a particular Dockerfile variant and run the repository test suites inside the resulting container, execute the helper script and point it at the Dockerfile you want to exercise:

```bash
./build_and_test.sh docker/variants/Dockerfile.cyclic-1
```

The script builds the chosen image, runs the main `testing/` suite, and then executes any workflow harness tests bundled under `.github/workflows/tests` if that directory exists.

## Variant catalog

The `docker/variants` directory contains intentionally broken configurations. The `minimal-*` files omit dependencies entirely, the `missing-deps-*` files install conflicting toolchains, and the `cyclic-*` files ship toy libraries whose imports deadlock at runtime. None of them should be treated as production ready.
