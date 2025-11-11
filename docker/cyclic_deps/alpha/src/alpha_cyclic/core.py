from beta_cyclic.bridge import summon_beta


def make_alpha():
    """Return a value pulled through the beta bridge to demonstrate a circular import."""
    beta_payload = summon_beta()
    return f"alpha<{beta_payload}>"
