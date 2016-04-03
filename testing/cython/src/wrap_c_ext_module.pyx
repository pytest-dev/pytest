
cdef extern from "../clib/sqrc.c":
    int isqr(int a)
    double dsqr(double a)


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
        return isqr(a)

    elif isinstance(a, (float, )):
        return dsqr(a)

    else:
        raise TypeError("Expected int or float type input.")
