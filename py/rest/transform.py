import py
from py.__.rest import rst
from py.xml import html

class RestTransformer(object):
    def __init__(self, tree):
        self.tree = tree
        self._titledepths = {}
        self._listmarkers = []

    def parse(self, handler):
        handler.startDocument()
        self.parse_nodes(self.tree.children, handler)
        handler.endDocument()

    def parse_nodes(self, nodes, handler):
        for node in nodes:
            name = node.__class__.__name__
            if name == 'Rest':
                continue
            getattr(self, 'handle_%s' % (name,))(node, handler)

    def handle_Title(self, node, handler):
        depthkey = (node.abovechar, node.belowchar)
        if depthkey not in self._titledepths:
            if not self._titledepths:
                depth = 1
            else:
                depth = max(self._titledepths.values()) + 1
            self._titledepths[depthkey] = depth
        else:
            depth = self._titledepths[depthkey]
        handler.startTitle(depth)
        self.parse_nodes(node.children, handler)
        handler.endTitle(depth)

    def handle_ListItem(self, node, handler):
        # XXX oomph...
        startlist = False
        c = node.parent.children
        nodeindex = c.index(node)
        if nodeindex == 0:
            startlist = True
        else:
            prev = c[nodeindex - 1]
            if not isinstance(prev, rst.ListItem):
                startlist = True
            elif prev.indent < node.indent:
                startlist = True
        endlist = False
        if nodeindex == len(c) - 1:
            endlist = True
        else:
            next = c[nodeindex + 1]
            if not isinstance(next, rst.ListItem):
                endlist = True
            elif next.indent < node.indent:
                endlist = True
        type = isinstance(node, rst.OrderedListItem) and 'o' or 'u'
        handler.startListItem('u', startlist)
        self.parse_nodes(node.children, handler)
        handler.endListItem('u', endlist)

    def handle_Transition(self, node, handler):
        handler.handleTransition()

    def handle_Paragraph(self, node, handler):
        handler.startParagraph()
        self.parse_nodes(node.children, handler)
        handler.endParagraph()

    def handle_SubParagraph(self, node, handler):
        handler.startSubParagraph()
        self.parse_nodes(node.children, handler)
        handler.endSubParagraph()

    def handle_LiteralBlock(self, node, handler):
        handler.handleLiteralBlock(node._text)

    def handle_Text(self, node, handler):
        handler.handleText(node._text)

    def handle_Em(self, node, handler):
        handler.handleEm(node._text)

    def handle_Strong(self, node, handler):
        handler.handleStrong(node._text)

    def handle_Quote(self, node, handler):
        handler.handleQuote(node._text)

    def handle_Link(self, node, handler):
        handler.handleLink(node._text, node.target)

def entitize(txt):
    for char, repl in (('&', 'amp'), ('>', 'gt'), ('<', 'lt'), ('"', 'quot'),
                       ("'", 'apos')):
        txt = txt.replace(char, '&%s;' % (repl,))
    return txt

class HTMLHandler(object):
    def __init__(self, title='untitled rest document'):
        self.title = title
        self.root = None
        self.tagstack = []
        self._currlist = None

    def startDocument(self):
        h = html.html()
        self.head = head = html.head()
        self.title = title = html.title(self.title)
        self._push(h)
        h.append(head)
        h.append(title)
        self.body = body = html.body()
        self._push(body)

    def endDocument(self):
        self._pop() # body
        self._pop() # html
    
    def startTitle(self, depth):
        h = getattr(html, 'h%s' % (depth,))()
        self._push(h)

    def endTitle(self, depth):
        self._pop()

    def startParagraph(self):
        self._push(html.p())

    def endParagraph(self):
        self._pop()

    def startSubParagraph(self):
        self._push(html.p(**{'class': 'sub'}))

    def endSubParagraph(self):
        self._pop()

    def handleLiteralBlock(self, text):
        pre = html.pre(text)
        if self.tagstack:
            self.tagstack[-1].append(pre)
        else:
            self.root = pre

    def handleText(self, text):
        self.tagstack[-1].append(text)

    def handleEm(self, text):
        self.tagstack[-1].append(html.em(text))

    def handleStrong(self, text):
        self.tagstack[-1].append(html.strong(text))

    def startListItem(self, type, startlist):
        if startlist:
            nodename = type == 'o' and 'ol' or 'ul'
            self._push(getattr(html, nodename)())
        self._push(html.li())

    def endListItem(self, type, closelist):
        self._pop()
        if closelist:
            self._pop()

    def handleLink(self, text, target):
        self.tagstack[-1].append(html.a(text, href=target))

    def _push(self, el):
        if self.tagstack:
            self.tagstack[-1].append(el)
        else:
            self.root = el
        self.tagstack.append(el)

    def _pop(self):
        self.tagstack.pop()

    def _html(self):
        return self.root.unicode()
    html = property(_html)

