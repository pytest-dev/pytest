
from py.xml import html

# HTML related stuff
class H(html):
    class Content(html.div):
        pass # style = html.Style(margin_left='15em')

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

    class Docstring(html.pre):
        style = html.Style(width='100%')
        pass

    class Navigation(html.div):
        #style = html.Style(min_height='99%', float='left', margin_top='1.2em',
        #                   overflow='auto', width='15em', white_space='nowrap')
        pass

    class NavigationItem(html.div):
        pass

    class BaseDescription(html.a):
        pass

    class SourceDef(html.div):
        pass

    class NonPythonSource(html.pre):
        pass # style = html.Style(margin_left='15em')

    class DirList(html.div):
        pass # style = html.Style(margin_left='15em')

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

