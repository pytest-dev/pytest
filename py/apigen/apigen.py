""" run 'py.test --apigen=<this script>' to get documentation exported

    exports to /tmp/output by default, set the environment variable
    'APIGEN_TARGET' to override
"""

import os
import py
import sys
from py.__.apigen import htmlgen
from py.__.apigen import linker
from py.__.apigen import project
from py.__.apigen.tracer.docstorage import pkg_to_dict

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
    # pkgdict['execnet.Channel'] = Channel  # XXX doesn't work 
    return pkgname, pkgdict

def build(pkgdir, dsa, capture):
    # create a linker (link database) for cross-linking
    l = linker.TempLinker()

    # create a project.Project instance to contain the LayoutPage instances
    proj = project.Project()

    # output dir
    if 'APIGEN_TARGET' in os.environ:
        targetdir = py.path.local(os.environ['APIGEN_TARGET'])
    else:
        targetdir = pkgdir.dirpath().join('apigen')
    targetdir.ensure(dir=True)

    # find out what to build
    all_names = dsa._get_names(filter=lambda x, y: True)
    namespace_tree = htmlgen.create_namespace_tree(all_names)

    # and build it
    apb = htmlgen.ApiPageBuilder(targetdir, l, dsa, pkgdir, namespace_tree,
                                 proj, capture, LayoutPage)
    spb = htmlgen.SourcePageBuilder(targetdir, l, pkgdir, proj, capture,
                                    LayoutPage)

    capture.err.writeorg('building namespace pages\n')
    apb.build_namespace_pages()

    capture.err.writeorg('building class pages\n')
    class_names = dsa.get_class_names()
    apb.build_class_pages(class_names)

    capture.err.writeorg('building function pages\n')
    function_names = dsa.get_function_names()
    apb.build_function_pages(function_names)

    capture.err.writeorg('building source pages\n')
    spb.build_pages(pkgdir)

    capture.err.writeorg('replacing temporary links\n')
    l.replace_dirpath(targetdir)

    capture.err.writeorg('done building documentation\n')

