
cdef int cfoo(int a, int b) except? -1
cdef int cbar(int a, int b) nogil except? -1
cdef inline int cspam(int a, int b) nogil except? -1


cdef class Eggs:
    cdef:
        readonly int a
        readonly int b

    cdef int foo(Eggs self) except? -1
    cdef int bar(Eggs self) nogil except? -1
    cdef int spam(Eggs self) nogil except? -1
    cpdef int fubar(Eggs self)
