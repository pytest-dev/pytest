def foo():
    """
    >>> foo()
    'bar'
    """
    return "bar"


def setup():
    # """
    # >>> setup()
    # 'ban'
    # """
    # return "ban"
    raise RuntimeError("Setup called!!! Oh No")
