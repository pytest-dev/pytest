# Troubleshooting Notes (Hard)

You can temporarily break the cycle by editing `/usr/local/lib/python*/site-packages/alpha_cyclic/core.py` to lazy-import `beta_cyclic` inside `make_alpha`. Doing so lets the interpreter finish initialization without infinite recursion.
