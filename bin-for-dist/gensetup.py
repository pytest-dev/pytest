import sys

sys.path.insert(0, sys.argv[1])
import py

toolpath = py.path.local(__file__)
binpath = py.path.local(py.__file__).dirpath('bin')

def error(msg):
    print >>sys.stderr, msg
    raise SystemExit, 1

def reformat(text):
    return " ".join(text.split())

class SetupWriter(object):
    EXCLUDES = ("MANIFEST.in", "contrib")

    def __init__(self, basedir, pkg, setuptools=False):
        self.basedir = basedir
        self.setuptools = setuptools
        assert self.basedir.check()
        self.pkg = pkg
        self.meta = pkg.__pkg__
        self.lines = []
        self.allpaths = self.getallpath(self.basedir)

    def getallpath(self, basedir):
        contrib = self.basedir.join("contrib")
        allpath = []
        lines = py.process.cmdexec("hg st -mcan").split("\n")
        for path in lines:
            p = basedir.join(path)
            assert p.check(), p
            if not p.relto(contrib) and p != contrib and not self.isexcluded(p):
                allpath.append(p)
        return allpath

    def append(self, string):
        lines = string.split("\n")
        while lines:
            if not lines[0].strip():
                lines.pop(0)
                continue
            break
        if not lines:
            self.lines.append("")
            return
        line = lines[0]
        indent = len(line) - len(line.lstrip())
        for line in lines:
            if line.strip():
                assert not line[:indent].strip(), line
                line = line[indent:]
            self.lines.append(line)

    def write_winfuncs(self):
        self.append('''
        ''')

    def tip_info(self, indent=8):
        old = self.basedir.chdir()
        indent = " " * indent
        try:
            info = []
            output = py.process.cmdexec(
                "hg tip --template '" # tags: {tags}\n"
                #"branch: {branches}\n"
                "revision: {rev}:{node}\n'"
            )
            for line in output.split("\n"):
                info.append("%s %s" %(indent, line.strip()))
            return "\n".join(info)
        finally:
            old.chdir()

    def setup_header(self):
        #tooltime = "%s %s" %(py.std.time.asctime(), py.std.time.tzname[0])
        toolname = toolpath.basename
        #toolrevision = py.path.svnwc(toolpath).info().rev

        pkgname = self.pkg.__name__
        self.append('"""py lib / py.test setup.py file"""')
        self.append('import os, sys')
        self.append("from setuptools import setup")

    def setup_trailer(self):
        self.append('''
            if __name__ == '__main__':
                main()
        ''')

    def setup_function(self):
        params = self.__dict__.copy()
        params.update(self.meta.__dict__)
        self.append('long_description = """')
        for line in params['long_description'].split('\n'):
            self.append(line)
        self.append('"""')
        trunk = None
        if params['version'] == 'trunk':
            trunk = 'trunk'
        self.append('trunk = %r' % trunk)
        self.append('''
            def main():
                setup(
                    name=%(name)r,
                    description=%(description)r,
                    long_description = long_description,
                    version= trunk or %(version)r,
                    url=%(url)r,
                    license=%(license)r,
                    platforms=%(platforms)r,
                    author=%(author)r,
                    author_email=%(author_email)r,
        ''' % params)
        indent = " " * 8
        self.append_pprint(indent, entry_points={'console_scripts':self.getconsolescripts()})
        self.append_pprint(indent, classifiers=self.meta.classifiers)
        self.append_pprint(indent, packages=self.getpackages())
        self.append_pprint(indent, package_data=self.getpackagedata())
        self.append_pprint(indent, zip_safe=True)
        self.append_pprint(indent, install_requires=['apipkg'])
        self.lines.append(indent[4:] + ")\n")

    def setup_scripts(self):
        # XXX this was used for a different approach
        not used
        self.append("""
            def getscripts():
                if sys.platform == "win32":
                    base = "py/bin/win32/"
                    ext = ".cmd"
                else:
                    base = "py/bin/"
                    ext = ""
                l = []
                for name in %r:
                    l.append(base + name + ext)
                return l
        """ % ([script.basename for script in binpath.listdir("py.*")]))

    def append_pprint(self, indent, append=",", **kw):
        for name, value in kw.items():
            stringio = py.std.StringIO.StringIO()
            value = py.std.pprint.pprint(value, stream=stringio)
            stringio.seek(0)
            lines =  stringio.readlines()
            line = lines.pop(0).rstrip()
            self.lines.append(indent + "%s=%s" %(name, line))
            indent = indent + " " * (len(name)+1)
            for line in lines:
                self.lines.append(indent + line.rstrip())
            self.lines[-1] = self.lines[-1] + append

    def getconsolescripts(self):
        bindir = self.basedir.join('py', 'bin')
        scripts = []
        for p in self.allpaths:
            if p.dirpath() == bindir:
                if p.basename.startswith('py.'):
                    shortname = "py" + p.basename[3:]
                    scripts.append("%s = py.cmdline:%s" %
                        (p.basename, shortname))
        return scripts

    def getscripts(self):
        bindir = self.basedir.join('py', 'bin')
        scripts = []
        for p in self.allpaths:
            if p.dirpath() == bindir:
                if p.basename.startswith('py.'):
                    scripts.append(p.relto(self.basedir))
        return scripts

    def getpackages(self):
        packages = []
        for p in self.allpaths: # contains no directories!
            #if p.basename == "py":
            #    continue
            if p.dirpath('__init__.py').check():
                modpath = p.dirpath().relto(self.basedir).replace(p.sep, '.')
                if modpath != "py" and not modpath.startswith("py."):
                    continue
                if modpath in packages:
                    continue
                for exclude in self.EXCLUDES:
                    if modpath.startswith(exclude):
                        print "EXCLUDING", modpath
                        break
                else:
                    packages.append(modpath)
        packages.sort()
        return packages

    def getpackagedata(self):
        datafiles = []
        pkgbase = self.basedir.join(self.pkg.__name__)
        for p in self.allpaths:
            if p.check(file=1) and (not p.dirpath("__init__.py").check()
               or p.ext != ".py"):
                if p.dirpath() != self.basedir:
                    x = p.relto(pkgbase)
                    if x:
                        datafiles.append(p.relto(pkgbase))
        return {'py': datafiles}

    def getdatafiles(self):
        datafiles = []
        for p in self.allpaths:
            if p.check(file=1) and not p.ext == ".py":
                if p.dirpath() != self.basedir:
                    datafiles.append(p.relto(self.basedir))
        return datafiles

    def setup_win32(self):
        import winpath
        self.append(py.std.inspect.getsource(winpath))
        self.append("""
            from distutils.command.install import install
            class my_install(install):
                def finalize_other(self):
                    install.finalize_other(self)
                    on_win32_add_to_PATH()
            cmdclass = {'install': my_install}
        """)

    def setup_win32(self):
        self.append(r'''
        # scripts for windows: turn "py.SCRIPT" into "py_SCRIPT" and create
        # "py.SCRIPT.cmd" files invoking "py_SCRIPT"
        from distutils.command.install_scripts import install_scripts
        class my_install_scripts(install_scripts):
            def run(self):
                install_scripts.run(self)
                #print self.outfiles
                for fn in self.outfiles:
                    basename = os.path.basename(fn)
                    if basename.startswith("py.") and not basename.endswith(".cmd"):
                        newbasename = basename.replace(".", "_")
                        newfn = os.path.join(os.path.dirname(fn), newbasename)
                        if os.path.exists(newfn):
                            os.remove(newfn)
                        os.rename(fn, newfn)
                        fncmd = fn + ".cmd"
                        if os.path.exists(fncmd):
                           os.remove(fncmd)
                        f = open(fncmd, 'w')
                        f.write("@echo off\n")
                        f.write('python "%%~dp0\%s" %%*' %(newbasename))
                        f.close()
        if sys.platform == "win32":
            cmdclass = {'install_scripts': my_install_scripts}
        else:
            cmdclass = {}
        ''')

    def write_setup(self):
        self.setup_header()
        self.setup_function()
        #self.setup_scripts()
        #self.setup_win32()
        self.setup_trailer()
        targetfile = self.basedir.join("setup.py")
        targetfile.write("\n".join(self.lines))
        print "wrote",  targetfile

    def isexcluded(self, wcpath):
        return wcpath.basename[0] == "."
        rel = wcpath.relto(self.basedir)
        if rel.find("testing") != -1:
            return True

    def write_manifest(self):
        lines = []
        for p in self.allpaths:
            if p.check(dir=1):
                continue
            toadd = p.relto(self.basedir)
            if toadd:
                for exclude in self.EXCLUDES:
                    if toadd.startswith(exclude):
                        break
                    assert toadd.find(exclude) == -1, (toadd, exclude)
                else:
                    lines.append("%s" %(toadd))
        lines.sort()
        targetfile = self.basedir.join("MANIFEST")
        targetfile.write("\n".join(lines))
        print "wrote",  targetfile

    def write_all(self):
        #self.write_manifest()
        self.write_setup()

def parseargs():
    basedir = py.path.local(sys.argv[1])
    if not basedir.check():
        error("basedir not found: %s" %(basedir,))
    pydir = basedir.join('py')
    if not pydir.check():
        error("no 'py' directory found in: %s" %(pydir,))
    actualpydir = py.path.local(py.__file__).dirpath()
    if pydir != actualpydir:
        error("package dir conflict, %s != %s" %(pydir, actualpydir))
    return basedir

def main(basedir=None):
    if basedir is None:
        basedir = parseargs()
    writer = SetupWriter(basedir, py, setuptools=True)
    writer.write_all()

if __name__ == "__main__":
    main()
