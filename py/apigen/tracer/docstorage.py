
""" This module is keeping track about API informations as well as
providing some interface to easily access stored data
"""

import py
import sys
import types
import inspect

from py.__.apigen.tracer.description import FunctionDesc, ClassDesc, \
                                            MethodDesc, Desc

from py.__.apigen.tracer import model

sorted = py.builtin.sorted

def pkg_to_dict(module):
    defs = module.__pkg__.exportdefs
    d = {}
    for key, value in defs.iteritems():
        chain = key.split('.')
        base = module
        # XXX generalize this:
        # a bit of special casing for greenlets which are
        # not available on all the platforms that python/py
        # lib runs
        try:
            for elem in chain:
                base = getattr(base, elem)
        except RuntimeError, exc:
            if elem == "greenlet":
                print exc.__class__.__name__, exc
                print "Greenlets not supported on this platform. Skipping apigen doc for this module"
                continue
            else:
                raise

        if value[1] == '*':
            d.update(get_star_import_tree(base, key))
        else:
            d[key] = base
    return d

def get_star_import_tree(module, modname):
    """ deal with '*' entries in an initpkg situation """
    ret = {}
    modpath = py.path.local(inspect.getsourcefile(module))
    pkgpath = module.__pkg__.getpath()
    for objname in dir(module):
        if objname.startswith('_'):
            continue # also skip __*__ attributes
        obj = getattr(module, objname)
        if (isinstance(obj, types.ClassType) or
                isinstance(obj, types.ObjectType)):
            try:
                sourcefile_object = py.path.local(
                                        inspect.getsourcefile(obj))
            except TypeError:
                continue
            else:
                if sourcefile_object.strpath != modpath.strpath:
                    # not in this package
                    continue
            dotted_name = '%s.%s' % (modname, objname)
            ret[dotted_name] = obj
    return ret
    
class DocStorage(object):
    """ Class storing info about API
    """
    def __init__(self):
        self.module_name = None

    def consider_call(self, frame, caller_frame, upward_cut_frame=None):
        assert isinstance(frame, py.code.Frame)
        desc = self.find_desc(frame.code, frame.raw.f_locals)
        if desc:
            self.generalize_args(desc, frame)
            desc.consider_call_site(caller_frame, upward_cut_frame)
            desc.consider_start_locals(frame)

    def generalize_args(self, desc, frame):
        args = [arg for key, arg in frame.getargs()]
        #self.call_stack.append((desc, args))
        desc.consider_call([model.guess_type(arg) for arg in args])
    
    def generalize_retval(self, desc, arg):
        desc.consider_return(model.guess_type(arg))

    def consider_return(self, frame, arg):
        assert isinstance(frame, py.code.Frame)
        desc = self.find_desc(frame.code, frame.raw.f_locals)
        if desc:
            self.generalize_retval(desc, arg)
            desc.consider_end_locals(frame)
    
    def consider_exception(self, frame, arg):
        desc = self.find_desc(frame.code, frame.raw.f_locals)
        if desc:
            exc_class, value, _ = arg
            desc.consider_exception(exc_class, value)

    def find_desc(self, code, locals):
        try:
            # argh, very fragile specialcasing
            return self.desc_cache[(code.raw,
                                    locals[code.raw.co_varnames[0]].__class__)]
        except (KeyError, IndexError, AttributeError): # XXX hrmph
            return self.desc_cache.get(code.raw, None)
        #for desc in self.descs.values():
        #    if desc.has_code(frame.code.raw):
        #        return desc
        #return None
    
    def make_cache(self):
        self.desc_cache = {}
        for key, desc in self.descs.iteritems():
            self.desc_cache[desc] = desc
    
    def from_dict(self, _dict, keep_frames=False, module_name=None):
        self.module_name = module_name
        self.descs = {}
        for key, val in _dict.iteritems():
            to_key, to_val = self.make_desc(key, val)
            if to_key:
                self.descs[to_key] = to_val
        self.make_cache()
        # XXX
        return self
    
    # XXX: This function becomes slowly outdated and even might go away at some
    #      point. The question is whether we want to use tracer.magic or not
    #      at all
    def add_desc(self, name, value, **kwargs):
        key = name
        count = 1
        while key in self.descs:
            key = "%s_%d" % (name, count)
            count += 1
        key, desc = self.make_desc(key, value, **kwargs)
        if key:
            self.descs[key] = desc
            self.desc_cache[desc] = desc
            return desc
        else:
            return None
        
    def make_desc(self, key, value, add_desc=True, **kwargs):
        if isinstance(value, types.FunctionType):
            desc = FunctionDesc(key, value, **kwargs)
        elif isinstance(value, (types.ObjectType, types.ClassType)):
            desc = ClassDesc(key, value, **kwargs)
            # XXX: This is the special case when we do not have __init__
            #      in dir(value) for uknown reason. Need to investigate it
            for name in dir(value) + ['__init__']:
                field = getattr(value, name, None)
                if isinstance(field, types.MethodType) and \
                    isinstance(field.im_func, types.FunctionType):
                    real_name = key + '.' + name
                    md = MethodDesc(real_name, field)
                    if add_desc: # XXX hack
                        self.descs[real_name] = md
                    desc.add_method_desc(name, md)
                # Some other fields as well?
        elif isinstance(value, types.MethodType):
            desc = MethodDesc(key, value, **kwargs)
        else:
            desc = Desc(value)
        return (key, desc) # How to do it better? I want a desc to be a key
            # value, but I cannot get full object if I do a lookup

    def from_pkg(self, module, keep_frames=False):
        self.module = module
        self.from_dict(pkg_to_dict(module), keep_frames, module.__name__)
        # XXX
        return self

    def from_module(self, func):
        raise NotImplementedError("From module")

class AbstractDocStorageAccessor(object):
    def __init__(self):
        raise NotImplementedError("Purely virtual object")
    
    def get_function_names(self):
        """ Returning names of all functions
        """
    
    def get_class_names(self):
        """ Returning names of all classess
        """

    def get_doc(self, name):
        """ Returning __doc__ of a function
        """

    def get_function_definition(self, name):
        """ Returns definition of a function (source)
        """
    
    def get_function_signature(self, name):
        """ Returns types of a function
        """

    def get_function_callpoints(self, name):
        """ Returns list of all callpoints
        """
    
    def get_module_name(self):
        pass
    
    def get_class_methods(self, name):
        """ Returns all methods of a class
        """
    
    #def get_object_info(self, key):
    #    
    
    def get_module_info(self):
        """ Returns module information
        """

class DocStorageAccessor(AbstractDocStorageAccessor):
    """ Set of helper functions to access DocStorage, separated in different
    class to keep abstraction
    """
    def __init__(self, ds):
        self.ds = ds

    def _get_names(self, filter):
        return [i for i, desc in self.ds.descs.iteritems() if filter(i, desc)]

    def get_function_names(self):
        return sorted(self._get_names(lambda i, desc: type(desc) is
                                                      FunctionDesc))
    
    def get_class_names(self):
        return sorted(self._get_names(lambda i, desc: isinstance(desc,
                                                                 ClassDesc)))
    
    #def get_function(self, name):
    #    return self.ds.descs[name].pyobj
    
    def get_doc(self, name):
        return self.ds.descs[name].pyobj.__doc__ or "*Not documented*"
    
    def get_function_definition(self, name):
        desc = self.ds.descs[name]
        assert isinstance(desc, FunctionDesc)
        code = py.code.Code(desc.code)
        return code.fullsource[code.firstlineno]
    
    def get_function_signature(self, name):
        desc = self.ds.descs[name]
        # we return pairs of (name, type) here
        names = desc.pyobj.func_code.co_varnames[
                    :desc.pyobj.func_code.co_argcount]
        types = desc.inputcells
        return zip(names, types), desc.retval
    
    def get_function_source(self, name):
        desc = self.ds.descs[name]
        try:
            return str(py.code.Source(desc.pyobj))
        except IOError:
            return "Cannot get source"

    def get_function_callpoints(self, name):
        # return list of tuple (filename, fileline, frame)
        return self.ds.descs[name].get_call_sites()

    def get_function_local_changes(self, name):
        return self.ds.descs[name].get_local_changes()

    def get_function_exceptions(self, name):
        return sorted([i.__name__ for i in self.ds.descs[name].exceptions.keys()])

    def get_module_name(self):
        if self.ds.module_name is not None:
            return self.ds.module_name
        elif hasattr(self.ds, 'module'):
            return self.ds.module.__name__
        return "Unknown module"
    
    def get_class_methods(self, name):
        desc = self.ds.descs[name]
        assert isinstance(desc, ClassDesc)
        return sorted(desc.getfields())
        
    def get_module_info(self):
        module = getattr(self.ds, 'module', None)
        if module is None:
            return "Lack of module info"
        try:
            retval = module.__doc__ or "*undocumented*"
            retval = module.__pkg__.description
            retval = module.__pkg__.long_description
        except AttributeError:
            pass
        return retval

    def get_type_desc(self, _type):
        # XXX We provide only classes here
        if not isinstance(_type, model.SomeClass):
            return None
        # XXX we might want to cache it at some point
        for key, desc in self.ds.descs.iteritems():
            if desc.pyobj == _type.cls:
                return key, 'class', desc.is_degenerated
        return None

    def get_method_origin(self, name):
        method = self.ds.descs[name].pyobj
        cls = method.im_class
        if not cls.__bases__:
            return self.desc_from_pyobj(cls, cls.__name__)
        curr = cls
        while curr:
            for base in curr.__bases__:
                basefunc = getattr(base, method.im_func.func_name, None)
                if (basefunc is not None and hasattr(basefunc, 'im_func') and
                        hasattr(basefunc.im_func, 'func_code') and
                        basefunc.im_func.func_code is
                            method.im_func.func_code):
                    curr = base
                    break
            else:
                break
        return self.desc_from_pyobj(curr, curr.__name__)

    def get_possible_base_classes(self, name):
        cls = self.ds.descs[name].pyobj
        if not hasattr(cls, '__bases__'):
            return []
        retval = []
        for base in cls.__bases__:
            desc = self.desc_from_pyobj(base, base.__name__)
            if desc is not None:
                retval.append(desc)
        return retval

    def desc_from_pyobj(self, pyobj, name):
        for desc in self.ds.descs.values():
            if isinstance(desc, ClassDesc) and desc.pyobj is pyobj:
                return desc
        # otherwise create empty desc
        key, desc = self.ds.make_desc(name, pyobj, False)
        #self.ds.descs[key] = desc
        desc.is_degenerated = True
        # and make sure we'll not try to link to it directly
        return desc

    def get_obj(self, name):
        return self.ds.descs[name].pyobj

