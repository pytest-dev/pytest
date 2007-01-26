import py
import os
import inspect
from py.__.apigen.layout import LayoutPage
from py.__.apigen.source import browser as source_browser
from py.__.apigen.source import html as source_html
from py.__.apigen.tracer.description import is_private
from py.__.apigen.rest.genrest import split_of_last_part
from py.__.apigen.linker import relpath

sorted = py.builtin.sorted
html = py.xml.html
raw = py.xml.raw

# HTML related stuff
class H(html):
    class Content(html.div):
        style = html.Style(margin_left='15em')

    class Description(html.div):
        pass
    
    class NamespaceDescription(Description):
        pass

    class NamespaceItem(html.div):
        pass

    class NamespaceDef(html.h1):
        pass

    class ClassDescription(Description):
        pass

    class ClassDef(html.h1):
        pass

    class MethodDescription(Description):
        pass

    class MethodDef(html.h2):
        pass

    class FunctionDescription(Description):
        pass

    class FunctionDef(html.h2):
        pass

    class ParameterDescription(html.div):
        pass

    class Docstring(html.div):
        style = html.Style(white_space='pre', min_height='3em')

    class Navigation(html.div):
        style = html.Style(min_height='99%', float='left', margin_top='1.2em',
                           overflow='auto', width='15em', white_space='nowrap')

    class NavigationItem(html.div):
        pass

    class BaseDescription(html.a):
        pass

    class SourceDef(html.div):
        pass

    class NonPythonSource(html.pre):
        style = html.Style(margin_left='15em')

    class DirList(html.div):
        style = html.Style(margin_left='15em')

    class DirListItem(html.div):
        pass

    class ValueDescList(html.ul):
        def __init__(self, *args, **kwargs):
            super(H.ValueDescList, self).__init__(*args, **kwargs)

    class ValueDescItem(html.li):
        pass

    class CallStackDescription(Description):
        pass

    class CallStackItem(html.div):
        class_ = 'callstackitem'

def get_param_htmldesc(linker, func):
    """ get the html for the parameters of a function """
    import inspect
    # XXX copy and modify formatargspec to produce html
    return H.em(inspect.formatargspec(*inspect.getargspec(func)))

def build_navitem_html(linker, name, linkid, indent, selected):
    href = linker.get_lazyhref(linkid)
    navitem = H.NavigationItem((indent * 2 * u'\xa0'), H.a(name, href=href))
    if selected:
        navitem.attr.class_ = 'selected'
    return navitem

# some helper functionality
def source_dirs_files(fspath):
    """ returns a tuple (dirs, files) for fspath

        dirs are all the subdirs, files are the files which are interesting
        in building source documentation for a Python code tree (basically all
        normal files excluding .pyc and .pyo ones)

        all files and dirs that have a name starting with . are considered
        hidden
    """
    dirs = []
    files = []
    for child in fspath.listdir():
        if child.basename.startswith('.'):
            continue
        if child.check(dir=True):
            dirs.append(child)
        elif child.check(file=True):
            if child.ext in ['.pyc', '.pyo']:
                continue
            files.append(child)
    return sorted(dirs), sorted(files)

def create_namespace_tree(dotted_names):
    """ creates a tree (in dict form) from a set of dotted names
    """
    ret = {}
    for dn in dotted_names:
        path = dn.split('.')
        for i in xrange(len(path)):
            ns = '.'.join(path[:i])
            itempath = '.'.join(path[:i + 1])
            if ns not in ret:
                ret[ns] = []
            if itempath not in ret[ns]:
                ret[ns].append(itempath)
    return ret

def wrap_page(project, title, contentel, navel, outputpath, stylesheeturl,
              scripturls):
    page = LayoutPage(project, title, nav=navel, encoding='UTF-8',
                      stylesheeturl=stylesheeturl, scripturls=scripturls)
    page.set_content(contentel)
    here = py.magic.autopath().dirpath()
    style = here.join('style.css').read()
    outputpath.join('style.css').write(style)
    apijs = here.join('api.js').read()
    outputpath.join('api.js').write(apijs)
    return page

# the PageBuilder classes take care of producing the docs (using the stuff
# above)
class AbstractPageBuilder(object):
    def write_page(self, title, reltargetpath, project, tag, nav):
        targetpath = self.base.join(reltargetpath)
        stylesheeturl = relpath('%s/' % (targetpath.dirpath(),),
                                self.base.join('style.css').strpath)
        scripturls = [relpath('%s/' % (targetpath.dirpath(),),
                              self.base.join('api.js').strpath)]
        page = wrap_page(project, title,
                         tag, nav, self.base, stylesheeturl, scripturls)
        content = self.linker.call_withbase(reltargetpath, page.unicode)
        targetpath.ensure()
        targetpath.write(content.encode("utf8"))

class SourcePageBuilder(AbstractPageBuilder):
    """ builds the html for a source docs page """
    def __init__(self, base, linker, projroot):
        self.base = base
        self.linker = linker
        self.projroot = projroot
    
    def build_navigation(self, fspath):
        nav = H.Navigation()
        relpath = fspath.relto(self.projroot)
        path = relpath.split(os.path.sep)
        indent = 0
        # build links to parents
        if relpath != '':
            for i in xrange(len(path)):
                dirpath = os.path.sep.join(path[:i])
                abspath = self.projroot.join(dirpath).strpath
                if i == 0:
                    text = self.projroot.basename
                else:
                    text = path[i-1]
                nav.append(build_navitem_html(self.linker, text, abspath,
                                              indent, False))
                indent += 1
        # build siblings or children and self
        if fspath.check(dir=True):
            # we're a dir, build ourselves and our children
            dirpath = fspath
            nav.append(build_navitem_html(self.linker, dirpath.basename,
                                          dirpath.strpath, indent, True))
            indent += 1
        elif fspath.strpath == self.projroot.strpath:
            dirpath = fspath
        else:
            # we're a file, build our parent's children only
            dirpath = fspath.dirpath()
        diritems, fileitems = source_dirs_files(dirpath)
        for dir in diritems:
            nav.append(build_navitem_html(self.linker, dir.basename,
                                          dir.strpath, indent, False))
        for file in fileitems:
            selected = (fspath.check(file=True) and
                        file.basename == fspath.basename)
            nav.append(build_navitem_html(self.linker, file.basename,
                                          file.strpath, indent, selected))
        return nav

    re = py.std.re
    _reg_body = re.compile(r'<body[^>]*>(.*)</body>', re.S)
    def build_python_page(self, fspath):
        mod = source_browser.parse_path(fspath)
        # XXX let's cheat a bit here... there should be a different function 
        # using the linker, and returning a proper py.xml.html element,
        # at some point
        html = source_html.create_html(mod)
        snippet = self._reg_body.search(html).group(1)
        tag = H.SourceDef(raw(snippet))
        nav = self.build_navigation(fspath)
        return tag, nav

    def build_dir_page(self, fspath):
        tag = H.DirList()
        dirs, files = source_dirs_files(fspath)
        tag.append(H.h2('directories'))
        for path in dirs:
            tag.append(H.DirListItem(H.a(path.basename,
                            href=self.linker.get_lazyhref(str(path)))))
        tag.append(H.h2('files'))
        for path in files:
            tag.append(H.DirListItem(H.a(path.basename,
                            href=self.linker.get_lazyhref(str(path)))))
        nav = self.build_navigation(fspath)
        return tag, nav

    def build_nonpython_page(self, fspath):
        try:
            tag = H.NonPythonSource(unicode(fspath.read(), 'utf-8'))
        except UnicodeError:
            tag = H.NonPythonSource('no source available (binary file?)')
        nav = self.build_navigation(fspath)
        return tag, nav

    def prepare_pages(self, base):
        passed = []
        for fspath in [base] + list(base.visit()):
            if fspath.ext in ['.pyc', '.pyo']:
                continue
            relfspath = fspath.relto(base)
            if relfspath.find('%s.' % (os.path.sep,)) > -1:
                # skip hidden dirs and files
                continue
            elif fspath.check(dir=True):
                if relfspath != '':
                    relfspath += os.path.sep
                reloutputpath = 'source%s%sindex.html' % (os.path.sep,
                                                          relfspath)
            else:
                reloutputpath = "source%s%s.html" % (os.path.sep, relfspath)
            reloutputpath = reloutputpath.replace(os.path.sep, '/')
            outputpath = self.base.join(reloutputpath)
            self.linker.set_link(str(fspath), reloutputpath)
            passed.append((fspath, outputpath))
        return passed

    def build_pages(self, data, project, base):
        """ build syntax-colored source views """
        for fspath, outputpath in data:
            if fspath.check(ext='.py'):
                try:
                    tag, nav = self.build_python_page(fspath)
                except (KeyboardInterrupt, SystemError):
                    raise
                except: # XXX strange stuff going wrong at times... need to fix
                    exc, e, tb = py.std.sys.exc_info()
                    print '%s - %s' % (exc, e)
                    print
                    print ''.join(py.std.traceback.format_tb(tb))
                    print '-' * 79
                    del tb
                    tag, nav = self.build_nonpython_page(fspath)
            elif fspath.check(dir=True):
                tag, nav = self.build_dir_page(fspath)
            else:
                tag, nav = self.build_nonpython_page(fspath)
            title = 'sources for %s' % (fspath.basename,)
            reltargetpath = outputpath.relto(self.base).replace(os.path.sep, '/')
            self.write_page(title, reltargetpath, project, tag, nav)

class ApiPageBuilder(AbstractPageBuilder):
    """ builds the html for an api docs page """
    def __init__(self, base, linker, dsa, projroot, namespace_tree):
        self.base = base
        self.linker = linker
        self.dsa = dsa
        self.projroot = projroot
        self.projpath = py.path.local(projroot)
        self.namespace_tree = namespace_tree
        
    def build_callable_view(self, dotted_name):
        """ build the html for a class method """
        # XXX we may want to have seperate
        func = self.dsa.get_obj(dotted_name)
        docstring = func.__doc__
        localname = func.__name__
        argdesc = get_param_htmldesc(self.linker, func)
        valuedesc = self.build_callable_signature_description(dotted_name)

        sourcefile = inspect.getsourcefile(func)
        callable_source = self.dsa.get_function_source(dotted_name)
        # i assume they're both either available or unavailable(XXX ?)
        is_in_pkg = self.is_in_pkg(sourcefile)
        if is_in_pkg and sourcefile and callable_source:
            csource = H.div(H.br(),
                            H.a('source: %s' % (sourcefile,),
                                href=self.linker.get_lazyhref(sourcefile)),
                            H.br(),
                            H.SourceDef(H.pre(callable_source)))
        elif not is_in_pkg and sourcefile and callable_source:
            csource = H.div(H.br(),
                            H.em('source: %s' % (sourcefile,)),
                            H.br(),
                            H.SourceDef(H.pre(callable_source)))
        else:
            csource = H.SourceDef('could not get source file')

        csdiv = H.div(style='display: none')
        for cs, _ in self.dsa.get_function_callpoints(dotted_name):
            csdiv.append(self.build_callsite(dotted_name, cs))
        callstack = H.CallStackDescription(
            H.a('show/hide call sites',
                href='#',
                onclick='showhideel(getnextsibling(this)); return false;'),
            csdiv,
        )
        snippet = H.FunctionDescription(
            H.FunctionDef(localname, argdesc),
            H.Docstring(docstring or H.em('no docstring available')),
            H.div(H.a('show/hide info',
                      href='#',
                      onclick=('showhideel(getnextsibling(this));'
                               'return false;')),
                  H.div(valuedesc, csource, callstack, style='display: none',
                        class_='funcinfo')),
        )
        
        return snippet

    def build_class_view(self, dotted_name):
        """ build the html for a class """
        cls = self.dsa.get_obj(dotted_name)
        # XXX is this a safe check?
        try:
            sourcefile = inspect.getsourcefile(cls)
        except TypeError:
            sourcelink = 'builtin file, no source available'
        else:
            if sourcefile is None:
                sourcelink = H.div('no source available')
            else:
                if sourcefile[-1] in ['o', 'c']:
                    sourcefile = sourcefile[:-1]
                sourcelink = H.div(H.a('view source',
                    href=self.linker.get_lazyhref(sourcefile)))

        docstring = cls.__doc__
        methods = self.dsa.get_class_methods(dotted_name)
        basehtml = []
        bases = self.dsa.get_possible_base_classes(dotted_name)
        for base in bases:
            try:
                obj = self.dsa.get_obj(base.name)
            except KeyError:
                basehtml.append(base.name)
            else:
                href = self.linker.get_lazyhref(base.name)
                basehtml.append(H.BaseDescription(base.name, href=href))
            basehtml.append(',')
        if basehtml:
            basehtml.pop()
        basehtml.append('):')
        if not hasattr(cls, '__name__'):
            clsname = 'instance of %s' % (cls.__class__.__name__,)
        else:
            clsname = cls.__name__
        snippet = H.ClassDescription(
            # XXX bases HTML
            H.ClassDef('%s(' % (clsname,), *basehtml),
            H.Docstring(docstring or H.em('no docstring available')),
            sourcelink,
        )
        if methods:
            snippet.append(H.h2('methods:'))
            for method in methods:
                snippet += self.build_callable_view('%s.%s' % (dotted_name,
                                                    method))
        # XXX properties
        return snippet

    def build_namespace_view(self, namespace_dotted_name, item_dotted_names):
        """ build the html for a namespace (module) """
        try:
            obj = self.dsa.get_obj(namespace_dotted_name)
        except KeyError:
            docstring = None
        else:
            docstring = obj.__doc__
        snippet = H.NamespaceDescription(
            H.NamespaceDef(namespace_dotted_name),
            H.Docstring(docstring or H.em('no docstring available'))
        )
        for dotted_name in sorted(item_dotted_names):
            itemname = dotted_name.split('.')[-1]
            if is_private(itemname):
                continue
            snippet.append(
                H.NamespaceItem(
                    H.a(itemname,
                        href=self.linker.get_lazyhref(dotted_name)
                    )
                )
            )
        return snippet

    def prepare_class_pages(self, classes_dotted_names):
        passed = []
        for dotted_name in sorted(classes_dotted_names):
            parent_dotted_name, _ = split_of_last_part(dotted_name)
            try:
                sibling_dotted_names = self.namespace_tree[parent_dotted_name]
            except KeyError:
                # no siblings (built-in module or sth)
                sibling_dotted_names = []
            tag = H.Content(self.build_class_view(dotted_name))
            nav = self.build_navigation(dotted_name, False)
            reltargetpath = "api/%s.html" % (dotted_name,)
            self.linker.set_link(dotted_name, reltargetpath)
            passed.append((dotted_name, tag, nav, reltargetpath))
        return passed
        
    def build_class_pages(self, data, project):
        """ build the full api pages for a set of classes """
        for dotted_name, tag, nav, reltargetpath in data:
            title = 'api documentation for %s' % (dotted_name,)
            self.write_page(title, reltargetpath, project, tag, nav)

    def prepare_method_pages(self, method_dotted_names):
        # XXX note that even though these pages are still built, there's no nav
        # pointing to them anymore...
        passed = []
        for dotted_name in sorted(method_dotted_names):
            parent_dotted_name, _ = split_of_last_part(dotted_name)
            module_dotted_name, _ = split_of_last_part(parent_dotted_name)
            sibling_dotted_names = self.namespace_tree[module_dotted_name]
            tag = self.build_callable_view(dotted_name)
            nav = self.build_navigation(dotted_name, False)
            reltargetpath = "api/%s.html" % (dotted_name,)
            self.linker.set_link(dotted_name, reltargetpath)
            passed.append((dotted_name, tag, nav, reltargetpath))
        return passed

    def build_method_pages(self, data, project):
        for dotted_name, tag, nav, reltargetpath in data:
            title = 'api documentation for %s' % (dotted_name,)
            self.write_page(title, reltargetpath, project, tag, nav)

    def prepare_function_pages(self, method_dotted_names):
        passed = []
        for dotted_name in sorted(method_dotted_names):
            # XXX should we create a build_function_view instead?
            parent_dotted_name, _ = split_of_last_part(dotted_name)
            sibling_dotted_names = self.namespace_tree[parent_dotted_name]
            tag = H.Content(self.build_callable_view(dotted_name))
            nav = self.build_navigation(dotted_name, False)
            reltargetpath = "api/%s.html" % (dotted_name,)
            self.linker.set_link(dotted_name, reltargetpath)
            passed.append((dotted_name, tag, nav, reltargetpath))
        return passed

    def build_function_pages(self, data, project):
        for dotted_name, tag, nav, reltargetpath in data:
            title = 'api documentation for %s' % (dotted_name,)
            self.write_page(title, reltargetpath, project, tag, nav)

    def prepare_namespace_pages(self):
        passed = []
        module_name = self.dsa.get_module_name().split('/')[-1]

        names = self.namespace_tree.keys()
        names.sort()
        function_names = self.dsa.get_function_names()
        class_names = self.dsa.get_class_names()
        for dotted_name in sorted(names):
            if dotted_name in function_names or dotted_name in class_names:
                continue
            subitem_dotted_names = self.namespace_tree[dotted_name]
            tag = H.Content(self.build_namespace_view(dotted_name,
                                                      subitem_dotted_names))
            nav = self.build_navigation(dotted_name, True)
            if dotted_name == '':
                reltargetpath = 'api/index.html'
            else:
                reltargetpath = 'api/%s.html' % (dotted_name,)
            self.linker.set_link(dotted_name, reltargetpath)
            passed.append((dotted_name, tag, nav, reltargetpath))
        return passed

    def build_namespace_pages(self, data, project):
        for dotted_name, tag, nav, reltargetpath in data:
            if dotted_name == '':
                dotted_name = self.dsa.get_module_name().split('/')[-1]
            title = 'index of %s namespace' % (dotted_name,)
            self.write_page(title, reltargetpath, project, tag, nav)

    def build_navigation(self, dotted_name, build_children=True):
        navitems = []

        # top namespace, index.html
        module_name = self.dsa.get_module_name().split('/')[-1]
        navitems.append(build_navitem_html(self.linker, module_name, '', 0,
                                           True))
        def build_nav_level(dotted_name, depth=1):
            navitems = []
            path = dotted_name.split('.')[:depth]
            siblings = self.namespace_tree.get('.'.join(path[:-1]))
            for dn in sorted(siblings):
                selected = dn == '.'.join(path)
                sibpath = dn.split('.')
                navitems.append(build_navitem_html(self.linker, sibpath[-1],
                                                   dn, depth,
                                                   selected))
                if selected:
                    lastlevel = dn.count('.') == dotted_name.count('.')
                    if not lastlevel:
                        navitems += build_nav_level(dotted_name, depth+1)
                    elif lastlevel and build_children:
                        # XXX hack
                        navitems += build_nav_level('%s.' % (dotted_name,),
                                                    depth+2)

            return navitems

        navitems += build_nav_level(dotted_name)
        return H.Navigation(*navitems)


    
        navitems = []

        # top namespace, index.html
        module_name = self.dsa.get_module_name().split('/')[-1]
        navitems.append(build_navitem_html(self.linker, module_name, '', 0,
                                           (selection == '')))

        indent = 1
        path = dotted_name.split('.')
        if dotted_name != '':
            # build html for each item in path to dotted_name item
            for i in xrange(len(path)):
                name = path[i]
                item_dotted_name = '.'.join(path[:i+1])
                selected = (selection == item_dotted_name)
                navitems.append(build_navitem_html(self.linker, name,
                                                   item_dotted_name, indent,
                                                   selected))
                indent += 1

        # build sub items of dotted_name item
        for item_dotted_name in py.builtin.sorted(item_dotted_names):
            itemname = item_dotted_name.split('.')[-1]
            if is_private(itemname):
                continue
            selected = (item_dotted_name == selection)
            navitems.append(build_navitem_html(self.linker, itemname,
                                               item_dotted_name, indent,
                                               selected))
        return H.Navigation(*navitems)

    def build_callable_signature_description(self, dotted_name):
        args, retval = self.dsa.get_function_signature(dotted_name)
        valuedesc = H.ValueDescList()
        for name, _type in args:
            valuedesc.append(self.build_sig_value_description(name, _type))
        if retval:
            retval = self.process_type_link(retval)
        ret = H.div(H.div('arguments:'), valuedesc, H.div('return value:'),
                    retval or 'None')
        return ret

    def build_sig_value_description(self, name, _type):
        l = self.process_type_link(_type)
        items = []
        next = "%s: " % name
        for item in l:
            if isinstance(item, str):
                next += item
            else:
                if next:
                    items.append(next)
                    next = ""
                items.append(item)
        if next:
            items.append(next)
        return H.ValueDescItem(*items)

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
            linktarget = self.linker.get_lazyhref(name)
            lst.append(H.a(str(_type), href=linktarget))
        else:
            raise IOError('do not think we ever get here?')
            # we should provide here some way of linking to sourcegen directly
            lst.append(name)
        return lst

    def is_in_pkg(self, sourcefile):
        return py.path.local(sourcefile).relto(self.projpath)

    def build_callsite(self, functionname, call_site):
        tbtag = self.gen_traceback(functionname, call_site)
        tag = H.CallStackItem(
            H.a("%s - line %s" % (call_site[0].filename, call_site[0].lineno + 1),
                href='#',
                onclick="showhideel(getnextsibling(this)); return false;"),
            H.div(tbtag, style='display: none')
        )
        return tag
    
    def gen_traceback(self, funcname, call_site):
        tbdiv = H.div()
        for line in call_site:
            lineno = line.lineno - line.firstlineno
            source = line.source
            sourcefile = line.filename
            mangled = []
            for i, sline in enumerate(str(source).split('\n')):
                if i == lineno:
                    l = '-> %s' % (sline,)
                else:
                    l = '   %s' % (sline,)
                mangled.append(l)
            if sourcefile:
                linktext = '%s - line %s' % (sourcefile, line.lineno + 1)
                # skip py.code.Source objects and source files outside of the
                # package
                if (not sourcefile.startswith('None') and
                        self.is_in_pkg(sourcefile)):
                    href = self.linker.get_lazyhref(sourcefile)
                    sourcelink = H.a(linktext, href=href)
                else:
                    sourcelink = H.div(linktext)
            else:
                sourcelink = H.div('source unknown')
            tbdiv.append(sourcelink)
            tbdiv.append(H.pre('\n'.join(mangled)))
        return tbdiv

