from py.__.rest.transform import HTMLHandler, entitize
from py.xml import html, raw

class PageHandler(HTMLHandler):
    def startDocument(self):
        super(PageHandler, self).startDocument()
        self.head.append(html.link(type='text/css', rel='stylesheet',
                                   href='style.css'))
        title = self.title[0]
        breadcrumb = ''.join([unicode(el) for el in self.breadcrumb(title)])
        self.body.append(html.div(raw(breadcrumb), class_='breadcrumb'))

    def handleLink(self, text, target):
        self.tagstack[-1].append(html.a(text, href=target,
                                        target='content'))

    def breadcrumb(self, title):
        if title != 'index':
            type, path = title.split('_', 1)
            path = path.split('.')
            module = None
            cls = None
            func = None
            meth = None
            if type == 'module':
                module = '.'.join(path)
            elif type == 'class':
                module = '.'.join(path[:-1])
                cls = path[-1]
            elif type  == 'method':
                module = '.'.join(path[:-2])
                cls = path[-2]
                meth = path[-1]
            else:
                module = '.'.join(path[:-1])
                func = path[-1]
            if module:
                yield html.a(module, href='module_%s.html' % (module,))
                if type != 'module':
                    yield u'.'
            if cls:
                s = cls
                if module:
                    s = '%s.%s' % (module, cls)
                yield html.a(cls, href='class_%s.html' % (s,))
                if type != 'class':
                    yield u'.'
            if meth:
                s = '%s.%s' % (cls, meth)
                if module:
                    s = '%s.%s.%s' % (module, cls, meth)
                yield html.a(meth, href='method_%s.html' % (s,))
            if func:
                s = func
                if module:
                    s = '%s.%s' % (module, func)
                yield html.a(func, href='function_%s.html' % (s,))

class IndexHandler(PageHandler):
    ignore_text = False

    def startDocument(self):
        super(IndexHandler, self).startDocument()
        self.head.append(html.script(type='text/javascript', src='apigen.js'))
        self._push(html.div(id='sidebar'))

    def endDocument(self):
        maindiv = html.div(id="main")
        maindiv.append(html.div(id="breadcrumb"))
        maindiv.append(html.iframe(name='content', id='content',
                                   src='module_py.html'))
        self.body.append(maindiv)
    
    def startTitle(self, depth):
        self.ignore_text = True
    
    def endTitle(self, depth):
        self.ignore_text = False

    def handleText(self, text):
        if self.ignore_text:
            return
        super(IndexHandler, self).handleText(text)

