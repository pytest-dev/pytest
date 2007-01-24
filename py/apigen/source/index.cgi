#!/usr/bin/python

import cgitb;cgitb.enable()
import path
import py
from py.__.apigen.source.browser import parse_path
from py.__.apigen.source.html import create_html, create_dir_html, \
                                     create_unknown_html

BASE_URL='http://codespeak.net/svn/py/dist'
def cgi_main():
    import os
    reqpath = os.environ.get('PATH_INFO', '')
    path = py.path.svnurl('%s%s' % (BASE_URL, reqpath))
    if not path.check():
        return create_unknown_html(path)
    if path.check(file=True):
        return unicode(create_html(parse_path(path)))
    elif path.check(dir=True):
        prefix = ''
        if not reqpath:
            prefix = 'index.cgi/'
        return create_dir_html(path, href_prefix=prefix)
    else:
        return create_unknown_html(path)

print 'Content-Type: text/html; charset=UTF-8'
print 
print cgi_main()
