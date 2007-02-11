
""" web server for displaying source
"""

import py
from pypy.translator.js.examples import server
from py.__.apigen.source.browser import parse_path
from py.__.apigen.source.html import create_html, create_dir_html, create_unknown_html
from py.xml import html

class Handler(server.TestHandler):
    BASE_URL='http://codespeak.net/svn/py/dist'

    def __getattr__(self, attr):
        if attr == 'index':
            attr = ''
        url = self.BASE_URL + "/" + attr
        if url.endswith('_py'):
            url = url[:-3] + '.py'
        path = py.path.svnurl(url)
        if not path.check():
            def f(rev=None):
                return create_unknown_html(path)
            f.exposed = True
            f.func_name = attr
            return f
        def f(rev='HEAD'):
            path = py.path.svnurl(url, rev)
            # some try.. except.. here
            if path.check(file=True):
                return unicode(create_html(parse_path(path)))
            elif path.check(dir=True):
                return create_dir_html(path)
            else:
                return create_unknown_html(path)
        f.exposed = True
        f.func_name = attr
        return f

def _main():
    server.start_server(handler=Handler)

if __name__ == '__main__':
    _main()

