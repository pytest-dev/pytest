# Cyclic Dependency Demo Packages

This directory contains the toy packages that power the `Dockerfile.cyclic-*` variants:

- `alpha/` defines the `alpha_cyclic` package.
- `beta/` defines the `beta_cyclic` package.
- `startup_cyclic.py` stitches the two libraries together so that importing either one eventually loops back into the other.

The resulting dependency cycle allows every Docker image to build successfully, but the Python interpreter deadlocks when it tries to import the libraries at runtime.

## Running the docker-based tests

From the repository root, run the helper script and pass it the path to the variant you want to exercise. For example:

```bash
./build_and_test.sh docker/variants/Dockerfile.cyclic-1
```

The command builds the selected Dockerfile, then executes the main `testing/` suite plus any workflow-specific tests in `.github/workflows/tests` inside the container.
