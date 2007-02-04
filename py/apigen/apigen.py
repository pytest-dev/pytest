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
    l = linker.Linker()
    proj = project.Project()

    if 'APIGEN_TARGET' in os.environ:
        targetdir = py.path.local(os.environ['APIGEN_TARGET'])
    else:
        targetdir = pkgdir.dirpath().join('apigen')
    targetdir.ensure(dir=True)

    all_names = dsa._get_names(filter=lambda x, y: True)
    namespace_tree = htmlgen.create_namespace_tree(all_names)
    apb = htmlgen.ApiPageBuilder(targetdir, l, dsa, pkgdir, namespace_tree,
                                 capture)
    spb = htmlgen.SourcePageBuilder(targetdir, l, pkgdir, capture)

    capture.err.writeorg('preparing namespace pages\n')
    ns_data = apb.prepare_namespace_pages()
    capture.err.writeorg('preparing class pages\n')
    class_names = dsa.get_class_names()
    class_data = apb.prepare_class_pages(class_names)
    capture.err.writeorg('preparing function pages\n')
    function_names = dsa.get_function_names()
    func_data = apb.prepare_function_pages(function_names)
    capture.err.writeorg('preparing source pages\n')
    source_data = spb.prepare_pages(pkgdir)

    capture.err.writeorg('building namespace pages\n')
    apb.build_namespace_pages(ns_data, proj)
    capture.err.writeorg('building class pages\n')
    apb.build_class_pages(class_data, proj)
    capture.err.writeorg('building function pages\n')
    apb.build_function_pages(func_data, proj)
    capture.err.writeorg('building source pages\n')
    spb.build_pages(source_data, proj, pkgdir)
    capture.err.writeorg('done building documentation\n')

