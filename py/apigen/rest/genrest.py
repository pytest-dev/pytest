
""" Generating ReST output (raw, not python)
out of data that we know about function calls
"""

import py
import sys
import re

from py.__.apigen.tracer.docstorage import DocStorageAccessor
from py.__.rest.rst import * # XXX Maybe we should list it here
from py.__.apigen.tracer import model
from py.__.rest.transform import RestTransformer

def split_of_last_part(name):
    name = name.split(".")
    return ".".join(name[:-1]), name[-1]

class AbstractLinkWriter(object):
    """ Class implementing writing links to source code.
    There should exist various classes for that, different for Trac,
    different for CVSView, etc.
    """
    def getlinkobj(self, obj, name):
        return None
    
    def getlink(self, filename, lineno, funcname):
        raise NotImplementedError("Abstract link writer")
    
    def getpkgpath(self, filename):
        # XXX: very simple thing
        path = py.path.local(filename).dirpath()
        while 1:
            try:
                path.join('__init__.py').stat()
                path = path.dirpath()
            except py.error.ENOENT:
                return path
    
class ViewVC(AbstractLinkWriter):
    """ Link writer for ViewVC version control viewer
    """
    def __init__(self, basepath):
        # XXX: should try to guess from a working copy of svn
        self.basepath = basepath
    
    def getlink(self, filename, lineno, funcname):
        path = str(self.getpkgpath(filename))
        assert filename.startswith(path), (
            "%s does not belong to package %s" % (filename, path))
        relname = filename[len(path):]
        if relname.endswith('.pyc'):
            relname = relname[:-1]
        sep = py.std.os.sep
        if sep != '/':
            relname = relname.replace(sep, '/')
        return ('%s:%s' % (filename, lineno),
                self.basepath + relname[1:] + '?view=markup')
    
class SourceView(AbstractLinkWriter):
    def __init__(self, baseurl):
        self.baseurl = baseurl
        if self.baseurl.endswith("/"):
            self.baseurl = baseurl[:-1]

    def getlink(self, filename, lineno, funcname):
        if filename.endswith('.pyc'):
            filename = filename[:-1]
        if filename is None:
            return "<UNKNOWN>:%s" % funcname,""
        pkgpath = self.getpkgpath(filename)
        if not filename.startswith(str(pkgpath)):
            # let's leave it
            return "<UNKNOWN>:%s" % funcname,""
        
        relname = filename[len(str(pkgpath)):]
        if relname.endswith('.pyc'):
            relname = relname[:-1]
        sep = py.std.os.sep
        if sep != '/':
            relname = relname.replace(sep, '/')
        return "%s:%s" % (relname, funcname),\
            "%s%s#%s" % (self.baseurl, relname, funcname)

    def getlinkobj(self, name, obj):
        try:
            filename = sys.modules[obj.__module__].__file__
            return self.getlink(filename, 0, name)
        except AttributeError:
            return None

class DirectPaste(AbstractLinkWriter):
    """ No-link writer (inliner)
    """
    def getlink(self, filename, lineno, funcname):
        return ('%s:%s' % (filename, lineno), "")

class DirectFS(AbstractLinkWriter):
    """ Creates links to the files on the file system (for local docs)
    """
    def getlink(self, filename, lineno, funcname):
        return ('%s:%s' % (filename, lineno), 'file://%s' % (filename,))

class PipeWriter(object):
    def __init__(self, output=sys.stdout):
        self.output = output
    
    def write_section(self, name, rest):
        text = "Contents of file %s.txt:" % (name,)
        self.output.write(text + "\n")
        self.output.write("=" * len(text) + "\n")
        self.output.write("\n")
        self.output.write(rest.text() + "\n")

    def getlink(self, type, targetname, targetfilename):
        return '%s.txt' % (targetfilename,)

class DirWriter(object):
    def __init__(self, directory=None):
        if directory is None:
            self.directory = py.test.ensuretemp("rstoutput")
        else:
            self.directory = py.path.local(directory)
    
    def write_section(self, name, rest):
        filename = '%s.txt' % (name,)
        self.directory.ensure(filename).write(rest.text())

    def getlink(self, type, targetname, targetfilename):
        # we assume the result will get converted to HTML...
        return '%s.html' % (targetfilename,)

class FileWriter(object):
    def __init__(self, fpath):
        self.fpath = fpath
        self.fp = fpath.open('w+')
        self._defined_targets = []

    def write_section(self, name, rest):
        self.fp.write(rest.text())
        self.fp.flush()

    def getlink(self, type, targetname, targetbasename):
        # XXX problem: because of docutils' named anchor generation scheme,
        # a method Foo.__init__ would clash with Foo.init (underscores are 
        # removed)
        if targetname in self._defined_targets:
            return None
        self._defined_targets.append(targetname)
        targetname = targetname.lower().replace('.', '-').replace('_', '-')
        while '--' in targetname:
            targetname = targetname.replace('--', '-')
        if targetname.startswith('-'):
            targetname = targetname[1:]
        if targetname.endswith('-'):
            targetname = targetname[:-1]
        return '#%s-%s' % (type, targetname)

class HTMLDirWriter(object):
    def __init__(self, indexhandler, filehandler, directory=None):
        self.indexhandler = indexhandler
        self.filehandler = filehandler
        if directory is None:
            self.directory = py.test.ensuretemp('dirwriter')
        else:
            self.directory = py.path.local(directory)

    def write_section(self, name, rest):
        if name == 'index':
            handler = self.indexhandler
        else:
            handler = self.filehandler
        h = handler(name)
        t = RestTransformer(rest)
        t.parse(h)
        self.directory.ensure('%s.html' % (name,)).write(h.html)

    def getlink(self, type, targetname, targetfilename):
        return '%s.html' % (targetfilename,)

class RestGen(object):
    def __init__(self, dsa, linkgen, writer=PipeWriter()):
        #assert isinstance(linkgen, DirectPaste), (
        #                        "Cannot use different linkgen by now")
        self.dsa = dsa
        self.linkgen = linkgen
        self.writer = writer
        self.tracebacks = {}

    def write(self):
        """write the data to the writer"""
        modlist = self.get_module_list()
        classlist = self.get_class_list(module='')
        funclist = self.get_function_list()
        modlist.insert(0, ['', classlist, funclist])

        indexrest = self.build_index([t[0] for t in modlist])
        self.writer.write_section('index', Rest(*indexrest))
        
        self.build_modrest(modlist)
        
    def build_modrest(self, modlist):
        modrest = self.build_modules(modlist)
        for name, rest, classlist, funclist in modrest:
            mname = name
            if mname == '':
                mname = self.dsa.get_module_name()
            self.writer.write_section('module_%s' % (mname,),
                                      Rest(*rest))
            for cname, crest, cfunclist in classlist:
                self.writer.write_section('class_%s' % (cname,),
                                          Rest(*crest))
                for fname, frest, tbdata in cfunclist:
                    self.writer.write_section('method_%s' % (fname,),
                                              Rest(*frest))
                    for tbname, tbrest in tbdata:
                        self.writer.write_section('traceback_%s' % (tbname,),
                                                  Rest(*tbrest))
            for fname, frest, tbdata in funclist:
                self.writer.write_section('function_%s' % (fname,),
                                          Rest(*frest))
                for tbname, tbrest in tbdata:
                    self.writer.write_section('traceback_%s' % (tbname,),
                                              Rest(*tbrest))
    
    def build_classrest(self, classlist):
        classrest = self.build_classes(classlist)
        for cname, rest, cfunclist in classrest:
            self.writer.write_section('class_%s' % (cname,),
                                      Rest(*rest))
            for fname, rest in cfunclist:
                self.writer.write_section('method_%s' % (fname,),
                                          Rest(*rest))

    def build_funcrest(self, funclist):
        funcrest = self.build_functions(funclist)
        for fname, rest, tbdata in funcrest:
            self.writer.write_section('function_%s' % (fname,),
                                      Rest(*rest))
            for tbname, tbrest in tbdata:
                self.writer.write_section('traceback_%s' % (tbname,),
                                          Rest(*tbrest))

    def build_index(self, modules):
        rest = [Title('index', abovechar='=', belowchar='=')]
        rest.append(Title('exported modules:', belowchar='='))
        for module in modules:
            mtitle = module
            if module == '':
                module = self.dsa.get_module_name()
                mtitle = '%s (top-level)' % (module,)
            linktarget = self.writer.getlink('module', module,
                                             'module_%s' % (module,))
            rest.append(ListItem(Link(mtitle, linktarget)))
        return rest

    def build_modules(self, modules):
        ret = []
        for module, classes, functions in modules:
            mname = module
            if mname == '':
                mname = self.dsa.get_module_name()
            rest = [Title('module: %s' % (mname,), abovechar='=',
                                                   belowchar='='),
                    Title('index:', belowchar='=')]
            if classes:
                rest.append(Title('classes:', belowchar='^'))
                for cls, bases, cfunclist in classes:
                    linktarget = self.writer.getlink('class', cls,
                        'class_%s' % (cls,))
                    rest.append(ListItem(Link(cls, linktarget)))
            classrest = self.build_classes(classes)
            if functions:
                rest.append(Title('functions:', belowchar='^'))
                for func in functions:
                    if module:
                        func = '%s.%s' % (module, func)
                    linktarget = self.writer.getlink('function',
                                                     func,
                                                     'function_%s' % (func,))
                    rest.append(ListItem(Link(func, linktarget)))
            funcrest = self.build_functions(functions, module, False)
            ret.append((module, rest, classrest, funcrest))
        return ret
    
    def build_classes(self, classes):
        ret = []
        for cls, bases, functions in classes:
            rest = [Title('class: %s' % (cls,), belowchar='='),
                    LiteralBlock(self.dsa.get_doc(cls))]
            # link to source
            link_to_class = self.linkgen.getlinkobj(cls, self.dsa.get_obj(cls))
            if link_to_class:
                rest.append(Paragraph(Text("source: "), Link(*link_to_class)))
        
            if bases:
                rest.append(Title('base classes:', belowchar='^')),
                for base in bases:
                    rest.append(ListItem(self.make_class_link(base)))
            if functions:
                rest.append(Title('functions:', belowchar='^'))
                for (func, origin) in functions:
                    linktarget = self.writer.getlink('method',
                                                     '%s.%s' % (cls, func),
                                                     'method_%s.%s' % (cls,
                                                                       func))
                    rest.append(ListItem(Link('%s.%s' % (cls, func),
                                              linktarget)))
            funcrest = self.build_functions(functions, cls, True)
            ret.append((cls, rest, funcrest))
        return ret
    
    def build_functions(self, functions, parent='', methods=False):
        ret = []
        for function in functions:
            origin = None
            if methods:
                function, origin = function
            if parent:
                function = '%s.%s' % (parent, function)
            rest, tbrest = self.write_function(function, origin=origin,
                                               ismethod=methods)
            ret.append((function, rest, tbrest))
        return ret

    def get_module_list(self):
        visited = []
        ret = []
        for name in self.dsa.get_class_names():
            if '.' in name:
                module, classname = split_of_last_part(name)
                if module in visited:
                    continue
                visited.append(module)
                ret.append((module, self.get_class_list(module),
                                    self.get_function_list(module)))
        return ret

    def get_class_list(self, module):
        ret = []
        for name in self.dsa.get_class_names():
            classname = name
            if '.' in name:
                classmodule, classname = split_of_last_part(name)
                if classmodule != module:
                    continue
            elif module != '':
                continue
            bases = self.dsa.get_possible_base_classes(name)
            ret.append((name, bases, self.get_method_list(name)))
        return ret

    def get_function_list(self, module=''):
        ret = []
        for name in self.dsa.get_function_names():
            funcname = name
            if '.' in name:
                funcpath, funcname = split_of_last_part(name)
                if funcpath != module:
                    continue
            elif module != '':
                continue
            ret.append(funcname)
        return ret

    def get_method_list(self, classname):
        methodnames = self.dsa.get_class_methods(classname)
        return [(mn, self.dsa.get_method_origin('%s.%s' % (classname, mn)))
                for mn in methodnames]

    def process_type_link(self, _type):
        # now we do simple type dispatching and provide a link in this case
        lst = []
        data = self.dsa.get_type_desc(_type)
        if not data:
            for i in _type.striter():
                if isinstance(i, str):
                    lst.append(i)
                else:
                    lst += self.process_type_link(i)
            return lst
        name, _desc_type, is_degenerated = data
        if not is_degenerated:
            linktarget = self.writer.getlink(_desc_type, name,
                                             '%s_%s' % (_desc_type, name))
            lst.append(Link(str(_type), linktarget))
        else:
            # we should provide here some way of linking to sourcegen directly
            lst.append(name)
        return lst

    def write_function(self, functionname, origin=None, ismethod=False,
                       belowchar='-'):
        # XXX I think the docstring should either be split on \n\n and cleaned
        # from indentation, or treated as ReST too (although this is obviously
        # dangerous for non-ReST docstrings)...
        if ismethod:
            title = Title('method: %s' % (functionname,), belowchar=belowchar)
        else:
            title = Title('function: %s' % (functionname,),
                          belowchar=belowchar)
        
        lst = [title, LiteralBlock(self.dsa.get_doc(functionname)),
               LiteralBlock(self.dsa.get_function_definition(functionname))]
        link_to_function = self.linkgen.getlinkobj(functionname, self.dsa.get_obj(functionname))
        if link_to_function:
            lst.insert(1, Paragraph(Text("source: "), Link(*link_to_function)))
        
        opar = Paragraph(Strong('origin'), ":")
        if origin:
            opar.add(self.make_class_link(origin))
        else:
            opar.add(Text('<UNKNOWN>'))
        lst.append(opar)

        lst.append(Paragraph(Strong("where"), ":"))
        args, retval = self.dsa.get_function_signature(functionname)
        for name, _type in args + [('return value', retval)]:
            l = self.process_type_link(_type)
            items = []
            next = "%s :: " % name
            for item in l:
                if isinstance(item, str):
                    next += item
                else:
                    if next:
                        items.append(Text(next))
                        next = ""
                    items.append(item)
            if next:
                items.append(Text(next))
            lst.append(ListItem(*items))
        
        local_changes = self.dsa.get_function_local_changes(functionname)
        if local_changes:
            lst.append(Paragraph(Strong('changes in __dict__ after execution'), ":"))
            for k, changeset in local_changes.iteritems():
                lst.append(ListItem('%s: %s' % (k, ', '.join(changeset))))
        
        exceptions = self.dsa.get_function_exceptions(functionname)
        if exceptions:
            lst.append(Paragraph(Strong('exceptions that might appear during '
                                 'execution'), ":"))
            for exc in exceptions:
                lst.append(ListItem(exc))
                # XXX: right now we leave it alone
        
        # XXX missing implementation of dsa.get_function_location()
        #filename, lineno = self.dsa.get_function_location(functionname)
        #linkname, linktarget = self.linkgen.getlink(filename, lineno)
        #if linktarget:
        #    lst.append(Paragraph("Function source: ",
        #               Link(linkname, linktarget)))
        #else:
        source = self.dsa.get_function_source(functionname)
        if source:
            lst.append(Paragraph(Strong('function source'), ":"))
            lst.append(LiteralBlock(source))
        
        # call sites..
        call_sites = self.dsa.get_function_callpoints(functionname)
        tbrest = []
        if call_sites:
            call_site_title = Title("call sites:", belowchar='+')
            lst.append(call_site_title)
            
            # we have to think differently here. I would go for:
            # 1. A quick'n'dirty statement where call has appeared first 
            #    (topmost)
            # 2. Link to short traceback
            # 3. Link to long traceback
            for call_site, _ in call_sites:
                fdata, tbdata = self.call_site_link(functionname, call_site)
                lst += fdata
                tbrest.append(tbdata)
        
        return lst, tbrest

    def call_site_link(self, functionname, call_site):
        tbid, tbrest = self.gen_traceback(functionname, call_site)
        tbname = '%s.%s' % (functionname, tbid)
        linktarget = self.writer.getlink('traceback',
                                         tbname,
                                         'traceback_%s' % (tbname,))
        frest = [Paragraph("called in %s" % call_site[0].filename),
                 Paragraph(Link("traceback %s" % (tbname,),
                 linktarget))]
        return frest, (tbname, tbrest)
    
    def gen_traceback(self, funcname, call_site):
        tbid = len(self.tracebacks.setdefault(funcname, []))
        self.tracebacks[funcname].append(call_site)
        tbrest = [Title('traceback for %s' % (funcname,))]
        for line in call_site:
            lineno = line.lineno - line.firstlineno
            linkname, linktarget = self.linkgen.getlink(line.filename,
                                                        line.lineno + 1,
                                                        funcname)
            if linktarget:
                tbrest.append(Paragraph(Link(linkname, linktarget)))
            else:
                tbrest.append(Paragraph(linkname))
            try:
                source = line.source
            except IOError:
                source = "*cannot get source*"
            mangled = []
            for i, sline in enumerate(str(source).split('\n')):
                if i == lineno:
                    line = '-> %s' % (sline,)
                else:
                    line = '   %s' % (sline,)
                mangled.append(line)
            tbrest.append(LiteralBlock('\n'.join(mangled)))
        return tbid, tbrest

    def make_class_link(self, desc):
        if not desc or desc.is_degenerated:
            # create dummy link here, or no link at all
            return Strong(desc.name)
        else:
            linktarget = self.writer.getlink('class', desc.name,
                'class_%s' % (desc.name,))
            return Link(desc.name, linktarget)
