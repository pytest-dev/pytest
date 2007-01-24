
import new

def test_new_code_object_carries_filename_through():
    class mystr(str):
        pass
    filename = mystr("dummy")
    co = compile("hello\n", filename, 'exec')
    assert not isinstance(co.co_filename, mystr)
    c2 = new.code(co.co_argcount, co.co_nlocals, co.co_stacksize,
             co.co_flags, co.co_code, co.co_consts,
             co.co_names, co.co_varnames,
             filename,
             co.co_name, co.co_firstlineno, co.co_lnotab,
             co.co_freevars, co.co_cellvars)
    assert c2.co_filename is filename
