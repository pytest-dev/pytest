
import py
from py.__.apigen.tracer import model
from py.__.code.source import getsource

import types
import inspect
import copy

MAX_CALL_SITES = 20

set = py.builtin.set

def is_private(name):
    return name.startswith('_') and not name.startswith('__')

class CallFrame(object):
    def __init__(self, frame):
        self.filename = frame.code.raw.co_filename
        self.lineno = frame.lineno
        self.firstlineno = frame.code.firstlineno
        try:
            self.source = getsource(frame.code.raw)
        except IOError:
            self.source = "could not get to source"

    def _getval(self):
        return (self.filename, self.lineno)

    def __hash__(self):
        return hash(self._getval())

    def __eq__(self, other):
        return self._getval() == other._getval()

    def __ne__(self, other):
        return not self == other

class CallStack(object):
    def __init__(self, tb):
        #if isinstance(tb, py.code.Traceback):
        #    self.tb = tb
        #else:
        #    self.tb = py.code.Traceback(tb)
        self.tb = [CallFrame(frame) for frame in tb]
    
    #def _getval(self):
    #    return [(frame.code.raw.co_filename, frame.lineno+1) for frame
    #        in self]
    
    def __hash__(self):
        return hash(tuple(self.tb))
    
    def __eq__(self, other):
        return self.tb == other.tb
    
    def __ne__(self, other):
        return not self == other
    
    #def __getattr__(self, attr):
    #    return getattr(self.tb, attr)
    
    def __iter__(self):
        return iter(self.tb)
    
    def __getitem__(self, item):
        return self.tb[item]
    
    def __len__(self):
        return len(self.tb)
    
    def __cmp__(self, other):
        return cmp(self.tb, other.tb)

def cut_stack(stack, frame, upward_frame=None):
    if hasattr(frame, 'raw'):
        frame = frame.raw
    if upward_frame:
        if hasattr(upward_frame, 'raw'):
            upward_frame = upward_frame.raw
        lst = [py.code.Frame(i) for i in stack[stack.index(frame):\
                stack.index(upward_frame)+1]]
        if len(lst) > 1:
            return CallStack(lst[:-1])
        return CallStack(lst)
    return CallStack([py.code.Frame(i) for i in stack[stack.index(frame):]])

##class CallSite(object):
##    def __init__(self, filename, lineno):
##        self.filename = filename
##        self.lineno = lineno
##    
##    def get_tuple(self):
##        return self.filename, self.lineno
##    
##    def __hash__(self):
##        return hash((self.filename, self.lineno))
##    
##    def __eq__(self, other):
##        return (self.filename, self.lineno) == (other.filename, other.lineno)
##    
##    def __ne__(self, other):
##        return not self == other
##    
##    def __cmp__(self, other):
##        if self.filename < other.filename:
##            return -1
##        if self.filename > other.filename:
##            return 1
##        if self.lineno < other.lineno:
##            return -1
##        if self.lineno > other.lineno:
##            return 1
##        return 0
    
class NonHashableObject(object):
    def __init__(self, cls):
        self.cls = cls
    
    def __hash__(self):
        raise NotImplementedError("Object of type %s are unhashable" % self.cls)

class Desc(object):
    def __init__(self, name, pyobj, **kwargs):
        self.pyobj = pyobj
        self.is_degenerated = False
        self.name = name
        if type(self) is Desc:
            # do not override property...
            self.code = NonHashableObject(self.__class__) # dummy think that makes code unhashable
    # we make new base class instead of using pypy's one because
    # of type restrictions of pypy descs
    
    def __hash__(self):
        return hash(self.code)
    
    def __eq__(self, other):
        if isinstance(other, Desc):
            return self.code == other.code
        if isinstance(other, types.CodeType):
            return self.code == other
        if isinstance(other, tuple) and len(other) == 2:
            return self.code == other
        return False
    
    def __ne__(self, other):
        return not self == other
    # This set of functions will not work on Desc, because we need to
    # define code somehow

class FunctionDesc(Desc):
    def __init__(self, *args, **kwargs):
        super(FunctionDesc, self).__init__(*args, **kwargs)
        self.inputcells = [model.s_ImpossibleValue for i in xrange(self.\
            code.co_argcount)]
        self.call_sites = {}
        self.keep_frames = kwargs.get('keep_frames', False)
        self.frame_copier = kwargs.get('frame_copier', lambda x:x)
        self.retval = model.s_ImpossibleValue
        self.exceptions = {}
    
    def consider_call(self, inputcells):
        for cell_num, cell in enumerate(inputcells):
            self.inputcells[cell_num] = model.unionof(cell, self.inputcells[cell_num])

    def consider_call_site(self, frame, cut_frame):
        if len(self.call_sites) > MAX_CALL_SITES:
            return
        stack = [i[0] for i in inspect.stack()]
        cs = cut_stack(stack, frame, cut_frame)
        self.call_sites[cs] = cs
    
    def consider_exception(self, exc, value):
        self.exceptions[exc] = True
    
    def get_call_sites(self):
        # convinient accessor for various data which we keep there
        if not self.keep_frames:
            return [(key, val) for key, val in self.call_sites.iteritems()]
        else:
            lst = []
            for key, val in self.call_sites.iteritems():
                for frame in val:
                    lst.append((key, frame))
            return lst
    
    def consider_return(self, arg):
        self.retval = model.unionof(arg, self.retval)

    def consider_start_locals(self, frame):
        pass

    def consider_end_locals(self, frame):
        pass
    
    def getcode(self):
        return self.pyobj.func_code
    code = property(getcode)
    
    def get_local_changes(self):
        return {}
    
class ClassDesc(Desc):
    def __init__(self, *args, **kwargs):
        super(ClassDesc, self).__init__(*args, **kwargs)
        self.fields = {}
        # we'll gather informations about methods and possibly
        # other variables encountered here
    
    def getcode(self):
        # This is a hack. We're trying to return as much close to __init__
        # of us as possible, but still hashable object
        if hasattr(self.pyobj, '__init__'):
            if hasattr(self.pyobj.__init__, 'im_func') and \
                hasattr(self.pyobj.__init__.im_func, 'func_code'):
                result = self.pyobj.__init__.im_func.func_code
            else:
                result = self.pyobj.__init__
        else:
            result = self.pyobj
        try:
            hash(result)
        except KeyboardInterrupt, SystemExit:
            raise
        except: # XXX UUuuuu bare except here. What can it really rise???
            try:
                hash(self.pyobj)
                result = self.pyobj
            except:
                result = self
        return result
    code = property(getcode)
    
    def consider_call(self, inputcells):
        if '__init__' in self.fields:
            md = self.fields['__init__']
        else:
            md = MethodDesc(self.name + '.__init__', self.pyobj.__init__)
            self.fields['__init__'] = md
        md.consider_call(inputcells)
    
    def consider_return(self, arg):
        pass # we *know* what return value we do have
    
    def consider_exception(self, exc, value):
        if '__init__' in self.fields:
            md = self.fields['__init__']
        else:
            md = MethodDesc(self.name + '.__init__', self.pyobj.__init__)
            self.fields['__init__'] = md
        md.consider_exception(exc, value)

    def consider_start_locals(self, frame):
        if '__init__' in self.fields:
            md = self.fields['__init__']
            md.consider_start_locals(frame)

    def consider_end_locals(self, frame):
        if '__init__' in self.fields:
            md = self.fields['__init__']
            md.consider_end_locals(frame)
    
    def consider_call_site(self, frame, cut_frame):
        self.fields['__init__'].consider_call_site(frame, cut_frame)
    
    def add_method_desc(self, name, methoddesc):
        self.fields[name] = methoddesc
    
    def getfields(self):
        # return fields of values that has been used
        l = [i for i, v in self.fields.iteritems() if not is_private(i)]
        return l

    def getbases(self):
        bases = []
        tovisit = [self.pyobj]
        while tovisit:
            current = tovisit.pop()
            if current is not self.pyobj:
                bases.append(current)
            tovisit += [b for b in current.__bases__ if b not in bases]
        return bases
    bases = property(getbases)
    
##    def has_code(self, code):
##        # check __init__ method
##        return self.pyobj.__init__.im_func.func_code is code
##    
##    def consider_call(self, inputcells):
##        # special thing, make MethodDesc for __init__
##        
##
class MethodDesc(FunctionDesc):
    def __init__(self, *args, **kwargs):
        super(MethodDesc, self).__init__(*args, **kwargs)
        self.old_dict = {}
        self.changeset = {}

    # right now it's not different than method desc, only code is different
    def getcode(self):
        return self.pyobj.im_func.func_code
    code = property(getcode)
##    def has_code(self, code):
##        return self.pyobj.im_func.func_code is code

    def __hash__(self):
        return hash((self.code, self.pyobj.im_class))
    
    def __eq__(self, other):
        if isinstance(other, tuple):
            return self.code is other[0] and self.pyobj.im_class is other[1]
        if isinstance(other, MethodDesc):
            return self.pyobj is other.pyobj
        return False

    def consider_start_locals(self, frame):
        # XXX recursion issues?
        obj = frame.f_locals[self.pyobj.im_func.func_code.co_varnames[0]]
        try:
            if not obj:
                # static method
                return
        except AttributeError:
            return
        self.old_dict = self.perform_dict_copy(obj.__dict__)

    def perform_dict_copy(self, d):
        if d is None:
            return {}
        return d.copy()

    def consider_end_locals(self, frame):
        obj = frame.f_locals[self.pyobj.im_func.func_code.co_varnames[0]]
        try:
            if not obj:
                # static method
                return
        except AttributeError:
            return
        # store the local changes
        # update self.changeset
        self.update_changeset(obj.__dict__)

    def get_local_changes(self):
        return self.changeset
    
    def set_changeset(changeset, key, value):
        if key not in changeset:
            changeset[key] = set([value])
        else:
            changeset[key].add(value)
    set_changeset = staticmethod(set_changeset)
    
    def update_changeset(self, new_dict):
        changeset = self.changeset
        for k, v in self.old_dict.iteritems():
            if k not in new_dict:
                self.set_changeset(changeset, k, "deleted")
            elif new_dict[k] != v:
                self.set_changeset(changeset, k, "changed")
        for k, v in new_dict.iteritems():
            if k not in self.old_dict:
                self.set_changeset(changeset, k, "created")
        return changeset

