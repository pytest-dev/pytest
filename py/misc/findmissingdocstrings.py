#!/usr/bin/env python 

import py
import inspect
import types

def report_strange_docstring(name, obj):
    if obj.__doc__ is None:
        print "%s misses a docstring" % (name, )
    elif obj.__doc__ == "":
        print "%s has an empty" % (name, )
    elif "XXX" in obj.__doc__:
        print "%s has an 'XXX' in its docstring" % (name, )

def find_code(method):
    return getattr(getattr(method, "im_func", None), "func_code", None)

def report_different_parameter_names(name, cls):
    bases = cls.__mro__
    for base in bases:
        for attr in dir(base):
            meth1 = getattr(base, attr)
            code1 = find_code(meth1)
            if code1 is None:
                continue
            if not callable(meth1):
                continue
            if not hasattr(cls, attr):
                continue
            meth2 = getattr(cls, attr)
            code2 = find_code(meth2)
            if not callable(meth2):
                continue
            if code2 is None:
                continue
            args1 = inspect.getargs(code1)[0]
            args2 = inspect.getargs(code2)[0]
            for a1, a2 in zip(args1, args2):
                if a1 != a2:
                    print "%s.%s have different argument names %s, %s than the version in %s" % (name, attr, a1, a2, base)


def find_all_exported():
    stack = [(name, getattr(py, name)) for name in dir(py)[::-1]
             if not name.startswith("_") and name != "compat"]
    seen = {}
    exported = []
    while stack:
        name, obj = stack.pop()
        if id(obj) in seen:
            continue
        else:
            seen[id(obj)] = True
        exported.append((name, obj))
        if isinstance(obj, type) or isinstance(obj, type(py)):
            stack.extend([("%s.%s" % (name, s), getattr(obj, s)) for s in dir(obj)
                           if len(s) <= 1 or not (s[0] == '_' and s[1] != '_')])
    return exported



if __name__ == '__main__':
    all_exported = find_all_exported()
    print "strange docstrings"
    print "=================="
    print
    for name, obj in all_exported:
        if callable(obj):
            report_strange_docstring(name, obj)
    print "\n\ndifferent parameters"
    print     "===================="
    print
    for name, obj in all_exported:
        if isinstance(obj, type):
            report_different_parameter_names(name, obj)
 
