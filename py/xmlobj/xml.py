"""
generic (and pythonic :-) xml tag and namespace objects 
""" 

class Tag(list):
    class Attr(object): 
        def __init__(self, **kwargs): 
            self.__dict__.update(kwargs) 

    def __init__(self, *args, **kwargs):
        super(Tag, self).__init__(args)
        self.attr = self.Attr(**kwargs) 

    def __unicode__(self):
        return self.unicode(indent=0) 

    def unicode(self, indent=2):
        from py.__.xmlobj.visit import SimpleUnicodeVisitor 
        l = []
        SimpleUnicodeVisitor(l.append, indent).visit(self) 
        return u"".join(l) 

    def __repr__(self):
        name = self.__class__.__name__ 
        return "<%r tag object %d>" % (name, id(self))

class raw(object):
    """just a box that can contain a unicode string that will be
    included directly in the output"""
    def __init__(self, uniobj):
        self.uniobj = uniobj

# the generic xml namespace 
# provides Tag classes on the fly optionally checking for
# a tagspecification 

class NamespaceMetaclass(type): 
    def __getattr__(self, name): 
        if name[:1] == '_': 
            raise AttributeError(name) 
        if self == Namespace: 
            raise ValueError("Namespace class is abstract") 
        tagspec = self.__tagspec__
        if tagspec is not None and name not in tagspec: 
            raise AttributeError(name) 
        classattr = {}
        if self.__stickyname__: 
            classattr['xmlname'] = name 
        cls = type(name, (self.__tagclass__,), classattr) 
        setattr(self, name, cls) 
        return cls 
        
class Namespace(object):
    __tagspec__ = None 
    __tagclass__ = Tag
    __metaclass__ = NamespaceMetaclass
    __stickyname__ = False 
       
