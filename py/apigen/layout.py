""" layout definition for generating api/source documents

    this is the place where customization can be done
"""

import py
from py.__.doc.confrest import Page

class LayoutPage(Page):
    """ this provides the layout and style information """

    def __init__(self, *args, **kwargs):
        self.nav = kwargs.pop('nav')
        super(LayoutPage, self).__init__(*args, **kwargs)

    def set_content(self, contentel):
        self.contentspace.append(contentel)

    def fill(self):
        super(LayoutPage, self).fill()
        self.menubar[:] = []
        self.menubar.append(self.nav)

