""" run 'py.test --apigen=<this script>' to get documentation exported
"""

import os
import py
import sys
from py.__.apigen import htmlgen
from py.__.apigen import linker
from py.__.apigen import project
from py.__.apigen.tracer.docstorage import pkg_to_dict
from py.__.doc.conftest import get_apigenpath

from layout import LayoutPage

def get_documentable_items_pkgdir(pkgdir):
    """ get all documentable items from an initpkg pkgdir
    
        this is a generic implementation, import as 'get_documentable_items'
        from your module when using initpkg to get all public stuff in the
        package documented
    """
    sys.path.insert(0, str(pkgdir.dirpath()))
    rootmod = __import__(pkgdir.basename)
    d = pkg_to_dict(rootmod)
    return pkgdir.basename, d

def get_documentable_items(pkgdir):
    pkgname, pkgdict = get_documentable_items_pkgdir(pkgdir)
    from py.__.execnet.channel import Channel
    pkgdict['execnet.Channel'] = Channel
    Channel.__apigen_hide_from_nav__ = True
    return pkgname, pkgdict

def sourcedirfilter(p):
    return ('.svn' not in str(p).split(p.sep) and
            not p.basename.startswith('.') and
            str(p).find('c-extension%sgreenlet%sbuild' % (p.sep, p.sep)) == -1)

def build(pkgdir, dsa, capture):
    # create a linker (link database) for cross-linking
    l = linker.TempLinker()

    # create a project.Project instance to contain the LayoutPage instances
    proj = project.Project()

    # output dir
    from py.__.conftest import option
    targetdir = get_apigenpath()
    targetdir.ensure(dir=True)

    # find out what to build
    all_names = dsa._get_names(filter=lambda x, y: True)
    namespace_tree = htmlgen.create_namespace_tree(all_names)

    # and build it
    apb = htmlgen.ApiPageBuilder(targetdir, l, dsa, pkgdir, namespace_tree,
                                 proj, capture, LayoutPage)
    spb = htmlgen.SourcePageBuilder(targetdir, l, pkgdir, proj, capture,
                                    LayoutPage, dirfilter=sourcedirfilter)

    apb.build_namespace_pages()
    class_names = dsa.get_class_names()
    apb.build_class_pages(class_names)
    function_names = dsa.get_function_names()
    apb.build_function_pages(function_names)
    spb.build_pages(pkgdir)
    l.replace_dirpath(targetdir)

