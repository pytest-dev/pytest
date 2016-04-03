
cdef int cfoo(int a, int b) except? -1:
    """
    >>> cfoo(1, 1)
    2
    """
    return a + b

cdef int cbar(int a, int b) nogil except? -1:
    """
    >>> cbar(1, 1)
    2
    """
    return a + b

cdef inline int cspam(int a, int b) nogil except? -1:
    """
    >>> cspam(1, 1)
    2
    """
    return (a + b)


cdef class Eggs:

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

    cdef int foo(Eggs self) except? -1:
        """
        >>> eggs = Eggs(1, 1)
        >>> eggs.foo()
        2
        """
        return self.a + self.b

    cdef int bar(Eggs self) nogil except? -1:
        """
        >>> eggs = Eggs(1, 1)
        >>> eggs.bar()
        2
        """
        return self.a + self.b

    cdef int spam(Eggs self) nogil except? -1:
        """
        >>> eggs = Eggs(1, 1)
        >>> eggs.spam()
        2
        """
        return cspam(self.a, self.b)

    cpdef int fubar(Eggs self):
        """
        >>> eggs = Eggs(1, 1)
        >>> eggs.fubar()
        2
        """
        return self.a + self.b

    def blarg(self):
        """
        >>> eggs = Eggs(1, 1)
        >>> eggs.blarg()
        2
        """
        return self.a + self.b
