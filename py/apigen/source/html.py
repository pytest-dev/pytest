
""" html - generating ad-hoc html out of source browser
"""

import py
from py.xml import html, raw
from compiler import ast
import time
from py.__.apigen.source.color import Tokenizer, PythonSchema
from py.__.apigen.source.browser import parse_path

class CompilationException(Exception):
    """ raised when something goes wrong while importing a module """

class HtmlEnchanter(object):
    def __init__(self, mod):
        self.mod = mod
        self.create_caches()
    
    def create_caches(self):
        mod = self.mod
        linecache = {}
        for item in mod.get_children():
            linecache[item.firstlineno] = item
        self.linecache = linecache
    
    def enchant_row(self, num, row):
        # add some informations to row, like functions defined in that
        # line, etc.
        try:
            item = self.linecache[num]
            # XXX: this should not be assertion, rather check, but we want to
            #      know if stuff is working
            pos = row.find(item.name)
            assert pos != -1
            end = len(item.name) + pos
            chunk = html.a(row[pos:end], href="#" + item.listnames(),
                     name=item.listnames())
            return [row[:pos], chunk, row[end:]]
        except KeyError:
            return [row] # no more info

def prepare_line(text, tokenizer, encoding):
    """ adds html formatting to text items (list)

        only processes items if they're of a string type (or unicode)
    """
    ret = []
    for item in text:
        if type(item) in [str, unicode]:
            tokens = tokenizer.tokenize(item)
            for t in tokens:
                if not isinstance(t.data, unicode):
                    data = unicode(t.data, encoding)
                else:
                    data = t.data
                if t.type in ['keyword', 'alt_keyword', 'number',
                              'string', 'comment']:
                    ret.append(html.span(data, class_=t.type))
                else:
                    ret.append(data)
        else:
            ret.append(item)
    return ret

def prepare_module(path, tokenizer, encoding):
    path = py.path.local(path)
    try:
        mod = parse_path(path)
    except:
        # XXX don't try to catch SystemExit: it's actually raised by one
        # of the modules in the py lib on import :(
        exc, e, tb = py.std.sys.exc_info()
        del tb
        raise CompilationException('while compiling %s: %s - %s' % (
                                    path, e.__class__.__name__, e))
    lines = [unicode(l, encoding) for l in path.readlines()]
    
    enchanter = HtmlEnchanter(mod)
    ret = []
    for i, line in enumerate(lines):
        text = enchanter.enchant_row(i + 1, line)
        if text == ['']:
            text = [raw('&#xa0;')]
        else:
            text = prepare_line(text, tokenizer, encoding)
        ret.append(text)
    return ret

class HTMLDocument(object):
    def __init__(self, encoding, tokenizer=None):
        self.encoding = encoding

        self.html = root = html.html()
        self.head = head = self.create_head()
        root.append(head)
        self.body = body = self.create_body()
        root.append(body)
        self.table, self.tbody = table, tbody = self.create_table()
        body.append(table)

        if tokenizer is None:
            tokenizer = Tokenizer(PythonSchema)
        self.tokenizer = tokenizer

    def create_head(self):
        return html.head(
            html.title('source view'),
            html.style("""
                body, td {
                    background-color: #FFF;
                    color: black;
                    font-family: monospace, Monaco;
                }

                table, tr {
                    margin: 0px;
                    padding: 0px;
                    border-width: 0px;
                }

                a {
                    color: blue;
                    font-weight: bold;
                    text-decoration: none;
                }
                
                a:hover {
                    color: #005;
                }
                
                .lineno {
                    text-align: right;
                    color: #555;
                    width: 3em;
                    padding-right: 1em;
                    border: 0px solid black;
                    border-right-width: 1px;
                }
                
                .code {
                    padding-left: 1em;
                    white-space: pre;
                }
                
                .comment {
                    color: purple;
                }

                .string {
                    color: #777;
                }

                .keyword {
                    color: blue;
                }

                .alt_keyword {
                    color: green;
                }
                
            """, type='text/css'),
        )

    def create_body(self):
        return html.body()

    def create_table(self):
        table = html.table(cellpadding='0', cellspacing='0')
        tbody = html.tbody()
        table.append(tbody)
        return table, tbody

    def add_row(self, lineno, text):
        if text == ['']:
            text = [raw('&#xa0;')]
        else:
            text = prepare_line(text, self.tokenizer, self.encoding)
        self.tbody.append(html.tr(html.td(str(lineno), class_='lineno'),
                                  html.td(class_='code', *text)))

    def __unicode__(self):
        # XXX don't like to use indent=0 here, but else py.xml's indentation
        # messes up the html inside the table cells (which displays formatting)
        return self.html.unicode(indent=0)

def create_html(mod):
    # out is some kind of stream
    #*[html.tr(html.td(i.name)) for i in mod.get_children()]
    lines = mod.path.open().readlines()
    
    enchanter = HtmlEnchanter(mod)
    enc = get_module_encoding(mod.path)
    doc = HTMLDocument(enc)
    for i, row in enumerate(lines):
        row = enchanter.enchant_row(i + 1, row)
        doc.add_row(i + 1, row)
    return unicode(doc)

style = html.style("""
  
  body, p, td {
    background-color: #FFF;
    color: black;
    font-family: monospace, Monaco;
  }

  td.type {
    width: 2em;
  }

  td.name {
    width: 30em;
  }

  td.mtime {
    width: 13em;
  }

  td.size {
    text-alignment: right;
  }

""")

def create_dir_html(path, href_prefix=''):
    h = html.html(
        html.head(
            html.title('directory listing of %s' % (path,)),
            style,
        ),
    )
    body = html.body(
        html.h1('directory listing of %s' % (path,)),
    )
    h.append(body)
    table = html.table()
    body.append(table)
    tbody = html.tbody()
    table.append(tbody)
    items = list(path.listdir())
    items.sort(key=lambda p: p.basename)
    items.sort(key=lambda p: not p.check(dir=True))
    for fpath in items:
        tr = html.tr()
        tbody.append(tr)
        td1 = html.td(fpath.check(dir=True) and 'D' or 'F', class_='type')
        tr.append(td1)
        href = fpath.basename
        if href_prefix:
            href = '%s%s' % (href_prefix, href)
        if fpath.check(dir=True):
            href += '/'
        td2 = html.td(html.a(fpath.basename, href=href), class_='name')
        tr.append(td2)
        td3 = html.td(time.strftime('%Y-%m-%d %H:%M:%S',
                      time.gmtime(fpath.mtime())), class_='mtime')
        tr.append(td3)
        if fpath.check(dir=True):
            size = ''
            unit = ''
        else:
            size = fpath.size()
            unit = 'B'
            for u in ['kB', 'MB', 'GB', 'TB']:
                if size > 1024:
                    size = round(size / 1024.0, 2)
                    unit = u
        td4 = html.td('%s %s' % (size, unit), class_='size')
        tr.append(td4)
    return unicode(h)

def create_unknown_html(path):
    h = html.html(
        html.head(
            html.title('Can not display page'),
            style,
        ),
        html.body(
            html.p('The data URL (%s) does not contain Python code.' % (path,))
        ),
    )
    return h.unicode()

_reg_enc = py.std.re.compile(r'coding[:=]\s*([-\w.]+)')
def get_module_encoding(path):
    if hasattr(path, 'strpath'):
        path = path.strpath
    if path[-1] in ['c', 'o']:
        path = path[:-1]
    fpath = py.path.local(path)
    fp = fpath.open()
    lines = []
    try:
        # encoding is only allowed in the first two lines
        for i in range(2):
            lines.append(fp.readline())
    finally:
        fp.close()
    match = _reg_enc.search('\n'.join(lines))
    if match:
        return match.group(1)
    return 'ISO-8859-1'

