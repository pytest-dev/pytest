""" layout definition for generating api/source documents

    this is the place where customization can be done
"""

import py
from py.__.doc import confrest
from py.__.apigen import linker

class LayoutPage(confrest.PyPage):
    """ this provides the layout and style information """

    stylesheets = [(py.path.local('../doc/style.css'), 'style.css'),
                   (py.path.local('style.css'), 'apigen_style.css')]
    scripts = [(py.path.local('api.js'), 'api.js')]

    def __init__(self, *args, **kwargs):
        self.nav = kwargs.pop('nav')
        self.relpath = kwargs.pop('relpath')
        super(LayoutPage, self).__init__(*args, **kwargs)

    def set_content(self, contentel):
        self.contentspace.append(contentel)

    def fill(self):
        super(LayoutPage, self).fill()
        #self.menubar[:] = []
        self.body.insert(0, self.nav)

    def setup_scripts_styles(self, copyto=None):
        for path, name in self.stylesheets:
            if copyto:
                copyto.join(name).write(path.read())
            self.head.append(py.xml.html.link(type='text/css',
                                              rel='stylesheet',
                                              href=self.relpath + name))
        for path, name in self.scripts:
            if copyto:
                copyto.join(name).write(path.read())
            self.head.append(py.xml.html.script(type="text/javascript",
                                                src=self.relpath + name))

