
import py
html = py.xml.html

# HTML related stuff
class H(html):
    class Content(html.div):
        def __init__(self, *args):
            super(H.Content, self).__init__(id='apigen-content', *args)

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

    class ClassDef(html.div):
        def __init__(self, classname, bases, docstring, sourcelink,
                     attrs, methods):
            header = H.h1('class %s(' % (classname,))
            for i, (name, href) in py.builtin.enumerate(bases):
                if i > 0:
                    header.append(', ')
                link = name
                if href is not None:
                    link = H.a(name, href=href)
                header.append(H.BaseDescription(link))
            header.append('):')
            super(H.ClassDef, self).__init__(header)
            self.append(H.div(H.Docstring(docstring or
                                          '*no docstring available*'),
                              sourcelink,
                              class_='classdoc'))
            if attrs:
                self.append(H.h2('class attributes and properties:'))
                for name, val in attrs:
                    self.append(H.PropertyDescription(name, val))
            if methods:
                self.append(H.h2('methods:'))
                for methodhtml in methods:
                    self.append(methodhtml)

    class MethodDescription(Description):
        pass

    class MethodDef(html.h2):
        pass

    class FunctionDescription(Description):
        def __init__(self, localname, argdesc, docstring, valuedesc, excdesc,
                     csource, callstack):
            infoid = 'info_%s' % (localname.replace('.', '_dot_'),)
            docstringid = 'docstring_%s' % (localname.replace('.', '_dot_'),)
            fd = H.FunctionDef(localname, argdesc,
                               title='click to view details',
                               onclick=('showhideel('
                                        'document.getElementById("%s")); '
                                         % (infoid,)))
            infodiv = H.div(
                H.Docstring(docstring or '*no docstring available*',
                            id=docstringid),
                H.FunctionInfo(valuedesc, excdesc, csource, callstack,
                               id=infoid, style="display: none"),
                class_='funcdocinfo')
            super(H.FunctionDescription, self).__init__(fd, infodiv)

    class FunctionDef(html.h2):
        style = html.Style(cursor='pointer')
        def __init__(self, name, argdesc, **kwargs):
            class_ = kwargs.pop('class_', 'funcdef')
            super(H.FunctionDef, self).__init__('def %s%s:' % (name, argdesc),
                                                class_=class_, **kwargs)

    class FunctionInfo(html.div):
        def __init__(self, valuedesc, excdesc, csource, callstack, **kwargs):
            super(H.FunctionInfo, self).__init__(valuedesc, H.br(), excdesc,
                                                 H.br(), csource,
                                                 callstack, class_='funcinfo',
                                                 **kwargs)
    
    class PropertyDescription(html.div):
        def __init__(self, name, value):
            if type(value) not in [str, unicode]:
                value = str(value)
            if len(value) > 100:
                value = value[:100] + '...'
            super(H.PropertyDescription, self).__init__(name, ': ',
                                                        H.em(value),
                                                        class_='property')

    class ParameterDescription(html.div):
        pass

    class Docstring(html.div):
        style = html.Style(white_space='pre', color='#666',
                           margin_left='1em', margin_bottom='1em')

    class Navigation(html.div):
        #style = html.Style(min_height='99%', float='left', margin_top='1.2em',
        #                   overflow='auto', width='15em', white_space='nowrap')
        pass

    class NavigationItem(html.div):
        def __init__(self, linker, linkid, name, indent, selected):
            href = linker.get_lazyhref(linkid)
            super(H.NavigationItem, self).__init__((indent * 2 * u'\xa0'),
                                                 H.a(name, href=href))
            if selected:
                self.attr.class_ = 'selected'

    class BaseDescription(html.span):
        pass

    class SourceSnippet(html.div):
        def __init__(self, text, href, sourceels=None):
            if sourceels is None:
                sourceels = []
            link = text
            if href:
                link = H.a(text, href=href)
            super(H.SourceSnippet, self).__init__(
                link, H.div(*sourceels))
    
    class PythonSource(Content):
        style = html.Style(font_size='0.8em')
        def __init__(self, *sourceels):
            super(H.PythonSource, self).__init__(
                H.div(*sourceels))

    class SourceBlock(html.table):
        def __init__(self):
            tbody = H.tbody()
            row = H.tr()
            tbody.append(row)
            linenocell = H.td(style='width: 1%')
            row.append(linenocell)
            linecell = H.td()
            row.append(linecell)
            
            self.linenotable = lntable = H.table()
            self.linenotbody = lntbody = H.tbody()
            lntable.append(lntbody)
            linenocell.append(lntable)

            self.linetable = ltable = H.table()
            self.linetbody = ltbody = H.tbody()
            ltable.append(ltbody)
            linecell.append(ltable)

            super(H.SourceBlock, self).__init__(tbody, class_='codeblock')

        def add_line(self, lineno, els):
            self.linenotbody.append(H.tr(H.td(lineno, class_='lineno')))
            self.linetbody.append(H.tr(H.td(H.pre(class_='code', *els),
                                            class_='codecell')))

    class NonPythonSource(Content):
        def __init__(self, *args):
            super(H.NonPythonSource, self).__init__(H.pre(*args))

    class DirList(Content):
        def __init__(self, dirs, files):
            dirs = [H.DirListItem(text, href) for (text, href) in dirs]
            files = [H.DirListItem(text, href) for (text, href) in files]
            super(H.DirList, self).__init__(
                H.h2('directories'), dirs,
                H.h2('files'), files,
            )

    class DirListItem(html.div):
        def __init__(self, text, href):
            super(H.DirListItem, self).__init__(H.a(text, href=href))

    class ValueDescList(html.ul):
        def __init__(self, *args, **kwargs):
            super(H.ValueDescList, self).__init__(*args, **kwargs)

    class ExceptionDescList(html.ul):
        def __init__(self, *args, **kwargs):
            super(H.ExceptionDescList, self).__init__(*args, **kwargs)

        def append(self, t):
            super(H.ExceptionDescList, self).append(html.li(t))

    class ValueDescItem(html.li):
        pass

    class CallStackDescription(Description):
        pass

    class CallStackLink(html.div):
        def __init__(self, filename, lineno, href):
            super(H.CallStackLink, self).__init__(
                H.a("stack trace %s - line %s" % (filename, lineno),
                    href=href))

    class Hideable(html.div):
        def __init__(self, name, class_, *content):
            super(H.Hideable, self).__init__(
                H.div(H.a('show/hide %s' % (name,),
                          href='#',
                          onclick=('showhideel(getnextsibling(this));'
                                   'return false;')),
                      H.div(style='display: none',
                            class_=class_,
                            *content)))

