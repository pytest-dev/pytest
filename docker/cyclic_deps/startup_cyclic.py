"""Startup hook that makes any Python interpreter import the circular packages immediately."""

from __future__ import annotations

from alpha_cyclic import make_alpha
from beta_cyclic import summon_beta


print("alpha", make_alpha())
print("beta", summon_beta())
