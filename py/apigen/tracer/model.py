
""" model - type system model for apigen
"""

# we implement all the types which are in the types.*, naming
# scheme after pypy's

import py
import types

set = py.builtin.set


# __extend__ and pairtype?
class SomeObject(object):
    typedef = types.ObjectType
    
    def __repr__(self):
        return "<%s>" % self.__class__.__name__[4:]
        return str(self.typedef)[7:-2]
    
    def unionof(self, other):
        if isinstance(other, SomeImpossibleValue):
            return self
        if isinstance(other, SomeUnion):
            return other.unionof(self)
        if self == other:
            return self
        return SomeUnion([self, other])
    
    def gettypedef(self):
        return self.typedef
    
    def __hash__(self):
        return hash(self.__class__)
    
    def __eq__(self, other):
        return self.__class__ == other.__class__
    
    def __ne__(self, other):
        return not self == other
        
    # this is to provide possibility of eventually linking some stuff
    def striter(self):
        yield str(self)

class SomeUnion(object):
    # empty typedef
    def __init__(self, possibilities):
        self.possibilities = set(possibilities)
    
    def unionof(self, other):
        if isinstance(other, SomeUnion):
            return SomeUnion(self.possibilities.union(other.possibilities))
        return SomeUnion(list(self.possibilities) + [other])
    
    def __eq__(self, other):
        if type(other) is not SomeUnion:
            return False
        return self.possibilities == other.possibilities
    
    def __ne__(self, other):
        return not self == other
    
    def __repr__(self):
        return "AnyOf(%s)" % ", ".join([str(i) for i in list(self.possibilities)])
    
    def gettypedef(self):
        return (None, None)
    
    def striter(self):
        yield "AnyOf("
        for num, i in enumerate(self.possibilities):
            yield i
            if num != len(self.possibilities) - 1:
                yield ", "
        yield ")"

class SomeBoolean(SomeObject):
    typedef = types.BooleanType

class SomeBuffer(SomeObject):
    typedef = types.BufferType

class SomeBuiltinFunction(SomeObject):
    typedef = types.BuiltinFunctionType

#class SomeBuiltinMethod(SomeObject):
#    typedef = types.BuiltinMethodType

class SomeClass(SomeObject):
    typedef = types.ClassType
    
    def __init__(self, cls):
        self.cls = cls
        self.name = cls.__name__
        self.id = id(cls)

    def __getstate__(self):
        return (self.name, self.id)

    def __setstate__(self, state):
        self.name, self.id = state
        self.cls = None
    
    def __hash__(self):
        return hash("Class") ^ hash(self.id)
    
    def __eq__(self, other):
        if type(other) is not SomeClass:
            return False
        return self.id == other.id
    
    def unionof(self, other):
        if type(other) is not SomeClass or self.id is not other.id:
            return super(SomeClass, self).unionof(other)
        return self
    
    def __repr__(self):
        return "Class %s" % self.name
    
class SomeCode(SomeObject):
    typedef = types.CodeType

class SomeComplex(SomeObject):
    typedef = types.ComplexType

class SomeDictProxy(SomeObject):
    typedef = types.DictProxyType

class SomeDict(SomeObject):
    typedef = types.DictType

class SomeEllipsis(SomeObject):
    typedef = types.EllipsisType

class SomeFile(SomeObject):
    typedef = types.FileType

class SomeFloat(SomeObject):
    typedef = types.FloatType

class SomeFrame(SomeObject):
    typedef = types.FrameType

class SomeFunction(SomeObject):
    typedef = types.FunctionType

class SomeGenerator(SomeObject):
    typedef = types.GeneratorType

class SomeInstance(SomeObject):
    def __init__(self, classdef):
        self.classdef = classdef
        
    def __hash__(self):
        return hash("SomeInstance") ^ hash(self.classdef)
    
    def __eq__(self, other):
        if type(other) is not SomeInstance:
            return False
        return other.classdef == self.classdef
    
    def unionof(self, other):
        if type(other) is not SomeInstance:
            return super(SomeInstance, self).unionof(other)
        if self.classdef == other.classdef:
            return self
        return SomeInstance(unionof(self.classdef, other.classdef))
    
    def __repr__(self):
        return "<Instance of %s>" % str(self.classdef)
    
    def striter(self):
        yield "<Instance of "
        yield self.classdef
        yield ">"
    
    typedef = types.InstanceType

class SomeInt(SomeObject):
    typedef = types.IntType

class SomeLambda(SomeObject):
    typedef = types.LambdaType

class SomeList(SomeObject):
    typedef = types.ListType

class SomeLong(SomeObject):
    typedef = types.LongType

class SomeMethod(SomeObject):
    typedef = types.MethodType

class SomeModule(SomeObject):
    typedef = types.ModuleType

class SomeNone(SomeObject):
    typedef = types.NoneType

class SomeNotImplemented(SomeObject):
    typedef = types.NotImplementedType

class SomeObject(SomeObject):
    typedef = types.ObjectType

class SomeSlice(SomeObject):
    typedef = types.SliceType

class SomeString(SomeObject):
    typedef = types.StringType

class SomeTraceback(SomeObject):
    typedef = types.TracebackType

class SomeTuple(SomeObject):
    typedef = types.TupleType

class SomeType(SomeObject):
    typedef = types.TypeType

class SomeUnboundMethod(SomeObject):
    typedef = types.UnboundMethodType

class SomeUnicode(SomeObject):
    typedef = types.UnicodeType

class SomeXRange(SomeObject):
    typedef = types.XRangeType

class SomeImpossibleValue(SomeObject):
    def unionof(self, other):
        return other
    
    def __repr__(self):
        return "<UNKNOWN>"

s_ImpossibleValue = SomeImpossibleValue()
s_None = SomeNone()
s_Ellipsis = SomeEllipsis()

def guess_type(x):
    # this is mostly copy of immutablevalue
    if hasattr(x, 'im_self') and x.im_self is None:
        x = x.im_func
        assert not hasattr(x, 'im_self')
    tp = type(x)
    if tp is bool:
        result = SomeBoolean()
    elif tp is int:
        result = SomeInt()
    elif issubclass(tp, str):
        result = SomeString()
    elif tp is unicode:
        result = SomeUnicode()
    elif tp is tuple:
        result = SomeTuple()
        #result = SomeTuple(items = [self.immutablevalue(e, need_const) for e in x])
    elif tp is float:
        result = SomeFloat()
    elif tp is list:
        #else:
        #    listdef = ListDef(self, s_ImpossibleValue)
        #    for e in x:
        #        listdef.generalize(self.annotation_from_example(e))
        result = SomeList()
    elif tp is dict:
##        dictdef = DictDef(self, 
##        s_ImpossibleValue,
##        s_ImpossibleValue,
##        is_r_dict = tp is r_dict)
##        if tp is r_dict:
##            s_eqfn = self.immutablevalue(x.key_eq)
##            s_hashfn = self.immutablevalue(x.key_hash)
##            dictdef.dictkey.update_rdict_annotations(s_eqfn,
##                s_hashfn)
##        for ek, ev in x.iteritems():
##            dictdef.generalize_key(self.annotation_from_example(ek))
##            dictdef.generalize_value(self.annotation_from_example(ev))
        result = SomeDict()
    elif tp is types.ModuleType:
        result = SomeModule()
    elif callable(x):
        #if hasattr(x, '__self__') and x.__self__ is not None:
        #    # for cases like 'l.append' where 'l' is a global constant list
        #    s_self = self.immutablevalue(x.__self__, need_const)
        #    result = s_self.find_method(x.__name__)
        #    if result is None:
        #        result = SomeObject()
        #elif hasattr(x, 'im_self') and hasattr(x, 'im_func'):
        #    # on top of PyPy, for cases like 'l.append' where 'l' is a
        #    # global constant list, the find_method() returns non-None
        #    s_self = self.immutablevalue(x.im_self, need_const)
        #    result = s_self.find_method(x.im_func.__name__)
        #else:
        #    result = None
        #if result is None:
        #    if (self.annotator.policy.allow_someobjects
        #        and getattr(x, '__module__', None) == '__builtin__'
        #        # XXX note that the print support functions are __builtin__
        #        and tp not in (types.FunctionType, types.MethodType)):
        ##        result = SomeObject()
        #        result.knowntype = tp # at least for types this needs to be correct
        #    else:
        #        result = SomePBC([self.getdesc(x)])
        if tp is types.BuiltinFunctionType or tp is types.BuiltinMethodType:
            result = SomeBuiltinFunction()
        elif hasattr(x, 'im_func'):
            result = SomeMethod()
        elif hasattr(x, 'func_code'):
            result = SomeFunction()
        elif hasattr(x, '__class__'):
            if x.__class__ is type:
                result = SomeClass(x)
            else:
                result = SomeInstance(SomeClass(x.__class__))
        elif tp is types.ClassType:
            result = SomeClass(x)
    elif x is None:
        return s_None
    elif hasattr(x, '__class__'):
        result = SomeInstance(SomeClass(x.__class__))
    else:
        result = SomeObject()
    # XXX here we might want to consider stuff like
    # buffer, slice, etc. etc. Let's leave it for now
    return result

def unionof(first, other):
    return first.unionof(other)
