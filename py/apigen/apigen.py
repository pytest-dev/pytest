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

def get_documentable_items(pkgdir):
    sys.path.insert(0, str(pkgdir.dirpath()))
    rootmod = __import__(pkgdir.basename)
    return 'py', pkg_to_dict(rootmod)

def build(pkgdir, dsa):
    l = linker.Linker()
    proj = project.Project()

    if 'APIGEN_TARGET' in os.environ:
        targetdir = py.path.local(os.environ['APIGEN_TARGET'])
    else:
        targetdir = pkgdir.dirpath().join('apigen')
    targetdir.ensure(dir=True)

    all_names = dsa._get_names(filter=lambda x, y: True)
    namespace_tree = htmlgen.create_namespace_tree(all_names)
    apb = htmlgen.ApiPageBuilder(targetdir, l, dsa, pkgdir, namespace_tree)
    spb = htmlgen.SourcePageBuilder(targetdir, l, pkgdir)

    ns_data = apb.prepare_namespace_pages()
    class_names = dsa.get_class_names()
    class_data = apb.prepare_class_pages(class_names)
    function_names = dsa.get_function_names()
    func_data = apb.prepare_function_pages(function_names)
    source_data = spb.prepare_pages(pkgdir)

    apb.build_namespace_pages(ns_data, proj)
    apb.build_class_pages(class_data, proj)
    #apb.build_method_pages(method_data, proj)
    apb.build_function_pages(func_data, proj)
    spb.build_pages(source_data, proj, pkgdir)

