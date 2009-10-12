#!/usr/bin/env python 

"""\
py.cleanup [PATH]

Delete pyc file recursively, starting from PATH (which defaults to the current
working directory). Don't follow links and don't recurse into directories with
a ".".
"""
import py

def main():
    parser = py.std.optparse.OptionParser(usage=__doc__)
    parser.add_option("-e", "--remove", dest="ext", default=".pyc", action="store",
        help="remove files with the given comma-separated list of extensions"
    )
    parser.add_option("-n", "--dryrun", dest="dryrun", default=False, 
        action="store_true", 
        help="display would-be-removed filenames"
    )
    parser.add_option("-d", action="store_true", dest="removedir",
                      help="remove empty directories")
    (options, args) = parser.parse_args()
    if not args:
        args = ["."]
    ext = options.ext.split(",")
    def shouldremove(p):
        return p.ext in ext
        
    for arg in args:
        path = py.path.local(arg)
        py.builtin.print_("cleaning path", path, "of extensions", ext)
        for x in path.visit(shouldremove, lambda x: x.check(dotfile=0, link=0)):
            remove(x, options)
    if options.removedir:
        for x in path.visit(lambda x: x.check(dir=1), 
                            lambda x: x.check(dotfile=0, link=0)):
            remove(x, options)

def remove(path, options):
    if options.dryrun:
        py.builtin.print_("would remove", path)
    else:
        py.builtin.print_("removing", path)
        path.remove()
                
