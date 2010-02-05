#!/usr/bin/env python 

"""\
py.cleanup [PATH] ...

Delete typical python development related files recursively under the specified PATH (which defaults to the current working directory). Don't follow links and don't recurse into directories with a dot.  Optionally remove setup.py related files and empty
directories. 

"""
import py
import sys, subprocess

def main():
    parser = py.std.optparse.OptionParser(usage=__doc__)
    parser.add_option("-e", metavar="ENDING", 
        dest="endings", default=[".pyc", "$py.class"], action="append", 
        help=("(multi) recursively remove files with the given ending." 
             " '.pyc' and '$py.class' are in the default list."))
    parser.add_option("-d", action="store_true", dest="removedir",
                      help="remove empty directories.")
    parser.add_option("-s", action="store_true", dest="setup",
                      help="remove 'build' and 'dist' directories next to setup.py files")
    parser.add_option("-a", action="store_true", dest="all",
                      help="synonym for '-S -d -e pip-log.txt'")
    parser.add_option("-n", "--dryrun", dest="dryrun", default=False, 
        action="store_true", 
        help="don't actually delete but display would-be-removed filenames.")
    (options, args) = parser.parse_args()

    Cleanup(options, args).main()

class Cleanup:
    def __init__(self, options, args):
        if not args:
            args = ["."]
        self.options = options
        self.args = [py.path.local(x) for x in args]
        if options.all:
            options.setup = True
            options.removedir = True
            options.endings.append("pip-log.txt")

    def main(self):
        if self.options.setup:
            for arg in self.args:
                self.setupclean(arg)
        
        for path in self.args:
            py.builtin.print_("cleaning path", path, 
                "of extensions", self.options.endings)
            for x in path.visit(self.shouldremove, self.recursedir):
                self.remove(x)
        if self.options.removedir:
            for x in path.visit(lambda x: x.check(dir=1), self.recursedir):
                if not x.listdir():
                    self.remove(x)

    def shouldremove(self, p):
        for ending in self.options.endings:
            if p.basename.endswith(ending):
                return True

    def recursedir(self, path):
        return path.check(dotfile=0, link=0)

    def remove(self, path):
        if not path.check():
            return
        if self.options.dryrun:
            py.builtin.print_("would remove", path)
        else:
            py.builtin.print_("removing", path)
            path.remove()

    def XXXcallsetup(self, setup, *args):
        old = setup.dirpath().chdir()
        try:
            subprocess.call([sys.executable, str(setup)] + list(args))
        finally:
            old.chdir()
            
    def setupclean(self, path):
        for x in path.visit("setup.py", self.recursedir):
            basepath = x.dirpath()
            self.remove(basepath / "build")
            self.remove(basepath / "dist")
