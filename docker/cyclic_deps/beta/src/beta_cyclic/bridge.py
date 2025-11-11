from alpha_cyclic.core import make_alpha


def summon_beta():
    """Intentionally call back into alpha, creating a circular runtime chain."""
    return f"beta<{make_alpha()}>"
