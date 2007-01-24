
""" test magic abilities of tracer
"""

import py
py.test.skip("These features have been disabled")

from py.__.apigen.tracer.magic import trace, get_storage, stack_copier, \
    DocStorageKeeper
from py.__.apigen.tracer.docstorage import DocStorage
from py.__.apigen.tracer import model

#def setup_function(f):
#    DocStorageKeeper.set_storage(DocStorage().from_dict({}))

def fun(a, b, c):
    return "a"
fun = trace()(fun)

def test_magic():
    fun(1, 2, 3)
    
    ds = get_storage()
    assert 'fun' in ds.descs
    assert len(ds.descs.keys()) == 2
    desc = ds.descs['fun']
    inputcells = desc.inputcells
    assert isinstance(inputcells[0], model.SomeInt)
    assert isinstance(inputcells[1], model.SomeInt)
    assert isinstance(inputcells[2], model.SomeInt)
    assert isinstance(desc.retval, model.SomeString)

def g(x):
    return f(x)

def f(x):
    return x + 3
f = trace(keep_frames=True, frame_copier=stack_copier)(f)

def test_fancy_copier():
    g(1)
    
    ds = get_storage()
    assert 'f' in ds.descs
    desc = ds.descs['f']
    stack = desc.call_sites.values()[0][0]
    assert str(stack[0].statement) == '    return f(x)'
    assert str(stack[1].statement) == '    g(1)'
