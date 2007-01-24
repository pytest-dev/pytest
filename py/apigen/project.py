""" this contains the code that actually builds the pages using layout.py

    building the docs happens in two passes: the first one takes care of
    collecting contents and navigation items, the second builds the actual
    HTML
"""

import py
from layout import LayoutPage

class Project(py.__.doc.confrest.Project):
    """ a full project

        this takes care of storing information on the first pass, and building
        pages + indexes on the second
    """

    def __init__(self):
        self.content_items = {}
    
    def add_item(self, path, content):
        """ add a single item (page)

            path is a (relative) path to the object, used for building links
            and navigation

            content is an instance of some py.xml.html item
        """
        assert path not in self.content_items, 'duplicate path %s' % (path,)
        self.content_items[path] = content

    def build(self, outputpath):
        """ convert the tree to actual HTML
        
            uses the LayoutPage class below for each page and takes care of
            building index documents for the root and each sub directory
        """
        opath = py.path.local(outputpath)
        opath.ensure(dir=True)
        paths = self.content_items.keys()
        paths.sort()
        for path in paths:
            # build the page using the LayoutPage class
            page = self.Page(self, path, stylesheeturl=self.stylesheet)
            page.contentspace.append(self.content_items[path])
            ipath = opath.join(path)
            if not ipath.dirpath().check():
                # XXX create index.html(?)
                ipath.ensure(file=True)
            ipath.write(page.unicode().encode(self.encoding))

    def process(self, txtpath):
        """ this allows using the project from confrest """
        # XXX not interesting yet, but who knows later (because of the
        # cool nav)

if __name__ == '__main__':
    # XXX just to have an idea of how to use this...
    proj = Project()
    here = py.path.local('.')
    for fpath in here.visit():
        if fpath.check(file=True):
            proj.add_item(fpath, convert_to_html_somehow(fpath))
    proj.build()

