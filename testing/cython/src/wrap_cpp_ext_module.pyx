# distutils: language = c++

cdef extern from "../clib/sqrcpp.cpp":
    T vsqr[T](T a)


def sqr(a):
    """
    >>> sqr(2)
    4
    >>> round(sqr(2.2), 2)
    4.84
    >>> sqr("asd")
    Traceback (most recent call last):
    ...
    TypeError: Expected int or float type input.
    """
    if isinstance(a, (int, )):
        return vsqr(<int>a)

    elif isinstance(a, (float, )):
        return vsqr(<double>a)

    else:
        raise TypeError("Expected int or float type input.")
