
""" source browser using compiler module

WARNING!!!

This is very simple and very silly attempt to make so.

"""

from compiler import parse, ast
import py

from py.__.path.common import PathBase

blockers = [ast.Function, ast.Class]

class BaseElem(object):
    def listnames(self):
        if getattr(self, 'parent', None):
            return self.parent.listnames() + '.' + self.name
        return self.name

class Module(BaseElem):
    def __init__(self, path, _dict):
        self.path = path
        self.dict = _dict
    
    def __getattr__(self, attr):
        try:
            return self.dict[attr]
        except KeyError:
            raise AttributeError(attr)
    
    def get_children(self):
        values = self.dict.values()
        all = values[:]
        for v in values:
            all += v.get_children()
        return all

def get_endline(start, lst):
    l = lst[::-1]
    for i in l:
        if i.lineno:
            return i.lineno
        end_ch = get_endline(None, i.getChildNodes())
        if end_ch:
            return end_ch
    return start

class Function(BaseElem):
    def __init__(self, name, parent, firstlineno, endlineno):
        self.firstlineno = firstlineno
        self.endlineno = endlineno
        self.name = name
        self.parent = parent

    def get_children(self):
        return []

class Method(BaseElem):
    def __init__(self, name, parent, firstlineno, endlineno):
        self.name = name
        self.firstlineno = firstlineno
        self.endlineno = endlineno
        self.parent = parent

def function_from_ast(ast, cls_ast, cls=Function):
    startline = ast.lineno
    endline = get_endline(startline, ast.getChildNodes())
    assert endline
    return cls(ast.name, cls_ast, startline, endline)

def class_from_ast(cls_ast):
    bases = [i.name for i in cls_ast.bases if isinstance(i, ast.Name)]
    # XXX
    methods = {}
    startline = cls_ast.lineno
    name = cls_ast.name
    endline = get_endline(startline, cls_ast.getChildNodes())
    cls = Class(name, startline, endline, bases, [])
    cls.methods = dict([(i.name, function_from_ast(i, cls, Method)) for i in \
        cls_ast.code.nodes if isinstance(i, ast.Function)])
    return cls

class Class(BaseElem):
    def __init__(self, name, firstlineno, endlineno, bases, methods):
        self.bases = bases
        self.firstlineno = firstlineno
        self.endlineno = endlineno
        self.name = name
        self.methods = methods

    def __getattr__(self, attr):
        try:
            return self.methods[attr]
        except KeyError:
            raise AttributeError(attr)
    
    def get_children(self):
        return self.methods.values()

def dir_nodes(st):
    """ List all the subnodes, which are not blockers
    """
    res = []
    for i in st.getChildNodes():
        res.append(i)
        if not i.__class__ in blockers:
            res += dir_nodes(i)
    return res

def update_mod_dict(imp_mod, mod_dict):
    # make sure that things that are in mod_dict, and not in imp_mod,
    # are not shown
    for key, value in mod_dict.items():
        if not hasattr(imp_mod, key):
            del mod_dict[key]

def parse_path(path):
    if not isinstance(path, PathBase):
        path = py.path.local(path)
    buf = path.open().read()
    st = parse(buf)
    # first go - we get all functions and classes defined on top-level
    nodes = dir_nodes(st)
    function_ast = [i for i in nodes if isinstance(i, ast.Function)]
    classes_ast = [i for i in nodes if isinstance(i, ast.Class)]
    mod_dict = dict([(i.name, function_from_ast(i, None)) for i in function_ast]
       + [(i.name, class_from_ast(i)) for i in classes_ast])
    # we check all the elements, if they're really there
    try:
        mod = path.pyimport()
    except (KeyboardInterrupt, SystemExit):
        raise
    except:  # catch all other import problems generically
        # XXX some import problem: we probably should not
        # pretend to have an empty module 
        pass
    else:
        update_mod_dict(mod, mod_dict)
    return Module(path, mod_dict)

