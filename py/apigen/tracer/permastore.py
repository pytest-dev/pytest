import py

class DescPlaceholder(object):
    pass

class ClassPlaceholder(object):
    pass

class SerialisableClassDesc(object):
    def __init__(self, original_desc):
        self.is_degenerated = original_desc.is_degenerated
        self.name = original_desc.name

class PermaDocStorage(object):
    """ Picklable version of docstorageaccessor
    """
    function_fields = ['source', 'signature', 'definition', 'callpoints',
                       'local_changes', 'exceptions']
    
    def __init__(self, dsa):
        """ Initialise from original doc storage accessor
        """
        self.names = {}
        self.module_info = dsa.get_module_info()
        self.module_name = dsa.get_module_name()
        self._save_functions(dsa)
        self._save_classes(dsa)

    def _save_functions(self, dsa):
        names = dsa.get_function_names()
        self.function_names = names
        for name in names:
            self._save_function(dsa, name)

    def _save_function(self, dsa, name):
        ph = DescPlaceholder()
        ph.__doc__ = dsa.get_doc(name)
        for field in self.function_fields:
            setattr(ph, field, getattr(dsa, 'get_function_%s' % field)(name))
        self.names[name] = ph
        return ph

    def _save_classes(self, dsa):
        names = dsa.get_class_names()
        self.class_names = names
        for name in names:
            ph = ClassPlaceholder()
            ph.__doc__ = dsa.get_doc(name)
            methods = dsa.get_class_methods(name)
            ph.methods = methods
            ph.base_classes = [SerialisableClassDesc(i) for i in
                               dsa.get_possible_base_classes(name)]

            for method in methods:
                method_name = name + "." + method
                mh = self._save_function(dsa, name + "." + method)
                mh.origin = SerialisableClassDesc(dsa.get_method_origin(
                    method_name))
            self.names[name] = ph

    def get_class_methods(self, name):
        desc = self.names[name]
        assert isinstance(desc, ClassPlaceholder)
        return desc.methods

    def get_doc(self, name):
        return self.names[name].__doc__

    def get_module_info(self):
        return self.module_info

    def get_module_name(self):
        return self.module_name

    def get_class_names(self):
        return self.class_names

    def get_function_names(self):
        return self.function_names

    def get_method_origin(self, name):
        # returns a DESCRIPTION of a method origin, to make sure where we
        # write it
        return self.names[name].origin

    def get_possible_base_classes(self, name):
        # returns list of descs of base classes
        return self.names[name].base_classes

    # This are placeholders to provide something more reliable
    def get_type_desc(self, _type):
        return None

    #def get_obj(self, name):
    #    This is quite hairy, get rid of it soon
    #    # returns a pyobj
    #    pass

for field in PermaDocStorage.function_fields:
    d = {"field": field}
    func_name = "get_function_%s" % (field, )
    exec py.code.Source("""
    def %s(self, name, field=field):
        return getattr(self.names[name], field)
""" % (func_name, )).compile() in d
    setattr(PermaDocStorage, func_name, d[func_name])
