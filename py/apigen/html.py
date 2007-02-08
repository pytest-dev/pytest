
from py.xml import html

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
                     properties, methods):
            header = H.h1('class %s(' % (classname,))
            for name, href in bases:
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
            if properties:
                self.append(H.h2('properties:'))
                for name, val in properties:
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
        def __init__(self, localname, argdesc, docstring, valuedesc, csource,
                     callstack):
            fd = H.FunctionDef(localname, argdesc)
            ds = H.Docstring(docstring or '*no docstring available*')
            fi = H.FunctionInfo(valuedesc, csource, callstack)
            super(H.FunctionDescription, self).__init__(fd, ds, fi)

    class FunctionDef(html.h2):
        def __init__(self, name, argdesc):
            super(H.FunctionDef, self).__init__('def %s%s:' % (name, argdesc))

    class FunctionInfo(html.div):
        def __init__(self, valuedesc, csource, callstack):
            super(H.FunctionInfo, self).__init__(
                H.Hideable('funcinfo', 'funcinfo', valuedesc, H.br(), csource,
                           callstack))
    
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

    class Docstring(html.pre):
        pass

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

    class BaseDescription(html.a):
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

    class SourceBlock(html.div):
        style = html.Style(margin_top='1em', margin_bottom='1em')
        def __init__(self):
            self.linenotable = lntable = H.table(style='float: left')
            self.linenotbody = lntbody = H.tbody()
            lntable.append(lntbody)

            self.linetable = ltable = H.table()
            self.linetbody = ltbody = H.tbody()
            ltable.append(ltbody)
            
            super(H.SourceBlock, self).__init__(lntable, ltable)

        def add_line(self, lineno, els):
            if els == []:
                els = [u'\xa0']
            self.linenotbody.append(H.tr(H.td(lineno, class_='lineno')))
            self.linetbody.append(H.tr(H.td(class_='code', *els)))

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

