

def foo(a, b):
    """
    >>> foo(1, 1)
    2
    """
    return a + b


class Eggs:

    def __init__(self, a, b):
        """
        >>> eggs = Eggs(1, 1)
        >>> eggs.a
        1
        >>> eggs.b
        1
        """
        self.a = a
        self.b = b

    def foo(self):
        """
        >>> eggs = Eggs(1, 1)
        >>> eggs.foo()
        2
        """
        return self.a + self.b
