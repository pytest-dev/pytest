
""" magic - some operations which helps to extend PDB with some magic data.
Actually there is only explicit tracking of data, might be extended to
automatic at some point.
"""

# some magic stuff to have singleton of DocStorage, but initialised explicitely

import weakref

import py
from py.__.apigen.tracer.docstorage import DocStorage
from py.__.apigen.tracer.tracer import Tracer
import sys

class DocStorageKeeper(object):
    doc_storage = DocStorage()
    doc_storage.tracer = Tracer(doc_storage)
    doc_storage.from_dict({})
    
    def set_storage(cl, ds):
        cl.doc_storage = ds
        cl.doc_storage.tracer = Tracer(ds)
    set_storage = classmethod(set_storage)

def get_storage():
    return DocStorageKeeper.doc_storage

def stack_copier(frame):
    # copy all stack, not only frame
    num = 0
    gather = False
    stack = []
    try:
        while 1:
            if gather:
                stack.append(py.code.Frame(sys._getframe(num)))
            else:
                if sys._getframe(num) is frame.raw:
                    gather = True
            num += 1
    except ValueError:
        pass
    return stack

def trace(keep_frames=False, frame_copier=lambda x:x):
    def decorator(fun):
        ds = get_storage()
        # in case we do not have this function inside doc storage, we
        # want to have it
        desc = ds.find_desc(py.code.Code(fun.func_code))
        if desc is None:
            desc = ds.add_desc(fun.func_name, fun, keep_frames=keep_frames,
                frame_copier=frame_copier)
        
        def wrapper(*args, **kwargs):
            ds.tracer.start_tracing()
            retval = fun(*args, **kwargs)
            ds.tracer.end_tracing()
            return retval
        
        return wrapper
    return decorator
