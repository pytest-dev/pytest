
import os, sys
WIDTH = 75

plugins = [
    ('advanced python testing', 
            'skipping mark pdb figleaf coverage '
            'monkeypatch capture recwarn tmpdir',),
    ('distributed testing, CI and deployment',
        'xdist pastebin junitxml resultlog genscript',),
    ('testing domains and conventions',
            'oejskit django unittest nose doctest restdoc'),
    ('internal, debugging, help functionality', 
          'helpconfig terminal hooklog')
    #('internal plugins / core functionality', 
    #    #'runner execnetcleanup # pytester',
    #    'runner execnetcleanup' # pytester',
    #)
]

externals = {
    'oejskit': "run javascript tests in real life browsers", 
    'xdist': None,
    'figleaf': None,
    'django': "for testing django applications", 
    'coverage': "for testing with Ned's coverage module ", 
    'xmlresult': "for generating xml reports " 
                 "and CruiseControl integration",
}

def warn(*args):
    msg = " ".join(map(str, args))
    print >>sys.stderr, "WARN:", msg

class RestWriter:
    _all_links = {}

    def __init__(self, target):
        self.target = py.path.local(target)
        self.links = []

    def _getmsg(self, args):
        return " ".join(map(str, args))

    def Print(self, *args, **kwargs):
        msg = self._getmsg(args)
        if 'indent' in kwargs:
            indent = kwargs['indent'] * " "
            lines = [(indent + x) for x in msg.split("\n")]
            msg = "\n".join(lines)
        self.out.write(msg)
        if not msg or msg[-1] != "\n":
            self.out.write("\n")
        self.out.flush()

    def sourcecode(self, source):
        lines = str(source).split("\n")
        self.Print(".. sourcecode:: python")
        self.Print()
        for line in lines:
            self.Print("   ", line)

    def _sep(self, separator, args):
        msg = self._getmsg(args)
        sep = len(msg) * separator
        self.Print()
        self.Print(msg)
        self.Print(sep)
        self.Print()


    def h1(self, *args):
        self._sep('=', args)

    def h2(self, *args):
        self._sep('-', args)

    def h3(self, *args):
        self._sep('+', args)

    def li(self, *args):
        msg = self._getmsg(args)
        sep = "* %s" %(msg)
        self.Print(sep)

    def dt(self, term):
        self.Print("``%s``" % term)

    def dd(self, doc):
        self.Print(doc, indent=4)

    def para(self, *args):
        msg = self._getmsg(args)
        self.Print(msg)

    def add_internal_link(self, name, path):
        relpath = path.new(ext=".html").relto(self.target.dirpath())
        self.links.append((name, relpath))

    def write_links(self):
        self.Print()
        self.Print(".. include:: links.txt")
        for link in self.links:
            key = link[0]
            if key in self._all_links:
                assert self._all_links[key] == link[1], (key, link[1])
            else:
                self._all_links[key] = link[1]
      
    def write_all_links(cls, linkpath):
        p = linkpath.new(basename="links.txt")
        p_writer = RestWriter(p)
        p_writer.out = p_writer.target.open("w")
        for name, value in cls._all_links.items():
            p_writer.Print(".. _`%s`: %s" % (name, value))
        p_writer.out.close()
        del p_writer.out
    write_all_links = classmethod(write_all_links)

    def make(self, **kwargs):
        self.out = self.target.open("w")
        self.makerest(**kwargs)
        self.write_links()

        self.out.close()
        print "wrote", self.target
        del self.out

class PluginOverview(RestWriter):
    def makerest(self, config):
        plugindir = py._pydir.join('plugin')
        for cat, specs in plugins:
            pluginlist = specs.split()
            self.h1(cat)
            for name in pluginlist:
                oneliner = externals.get(name, None)
                docpath = self.target.dirpath(name).new(ext=".txt")
                if oneliner is not None:
                    htmlpath = docpath.new(ext='.html')
                    self.para("%s_ (external) %s" %(name, oneliner))
                    self.add_internal_link(name, htmlpath)
                else:
                    doc = PluginDoc(docpath)
                    doc.make(config=config, name=name) 
                    self.add_internal_link(name, doc.target)
                    if name in externals:
                        self.para("%s_ (external) %s" %(name, doc.oneliner))
                    else:
                        self.para("%s_ %s" %(name, doc.oneliner))
                self.Print()

class HookSpec(RestWriter):
    def makerest(self, config):
        module = config.pluginmanager.hook._hookspecs
        source = py.code.Source(module)
        self.h1("hook specification sourcecode")
        self.sourcecode(source)

class PluginDoc(RestWriter):
    def makerest(self, config, name):
        config.pluginmanager.import_plugin(name)
        plugin = config.pluginmanager.getplugin(name)
        assert plugin is not None, plugin
        print plugin
        doc = plugin.__doc__.strip()
        i = doc.find("\n")
        if i == -1:
            oneliner = doc
            moduledoc = ""
        else:
            oneliner = doc[:i].strip()
            moduledoc = doc[i+1:].strip()

        self.name = oneliner # plugin.__name__.split(".")[-1]
        self.oneliner = oneliner 
        self.moduledoc = moduledoc
       
        #self.h1("%s plugin" % self.name) # : %s" %(self.name, self.oneliner))
        self.h1(oneliner)
        #self.Print(self.oneliner)
        self.Print()
        self.Print(".. contents::")
        self.Print("  :local:")
        self.Print()

        self.Print(moduledoc)
    
        self.emit_funcargs(plugin)
        self.emit_options(plugin)
        self.emit_source(plugin, config.hg_changeset)
        #self.sourcelink = (purename, 
        #    "http://bitbucket.org/hpk42/py-trunk/src/tip/py/test/plugin/" + 
        #    purename + ".py")
        #
    def emit_source(self, plugin, hg_changeset):
        basename = py.path.local(plugin.__file__).basename
        if basename.endswith("pyc"):
            basename = basename[:-1]
        #self.para("`%s`_ source code" % basename)
        #self.links.append((basename, 
        #    "http://bitbucket.org/hpk42/py-trunk/src/tip/py/test/plugin/" +
        #    basename))
        self.h1("Start improving this plugin in 30 seconds")
        self.para(py.code.Source("""
            1. Download `%s`_ plugin source code 
            2. put it somewhere as ``%s`` into your import path 
            3. a subsequent ``py.test`` run will use your local version

            Checkout customize_, other plugins_ or `get in contact`_. 
        """ % (basename, basename)))
        #    your work appreciated if you offer back your version.  In this case
        #    it probably makes sense if you `checkout the py.test 
        #    development version`_ and apply your changes to the plugin
        #    version in there. 
        #self.links.append((basename, 
        #    "http://bitbucket.org/hpk42/py-trunk/raw/%s/" 
        #    "py/test/plugin/%s" %(hg_changeset, basename)))
        self.links.append((basename, 
            "http://bitbucket.org/hpk42/py-trunk/raw/%s/" 
            "py/_plugin/%s" %(pyversion, basename)))
        self.links.append(('customize', '../customize.html'))
        self.links.append(('plugins', 'index.html'))
        self.links.append(('get in contact', '../../contact.html'))
        self.links.append(('checkout the py.test development version', 
            '../../install.html#checkout'))
       
        if 0: # this breaks the page layout and makes large doc files
            #self.h2("plugin source code") 
            self.Print()
            self.para("For your convenience here is also an inlined version "
                      "of ``%s``:" %basename)
            #self(or copy-paste from below)
            self.Print()
            self.sourcecode(py.code.Source(plugin))

    def emit_funcargs(self, plugin):
        funcargfuncs = []
        prefix = "pytest_funcarg__"
        for name in vars(plugin):
            if name.startswith(prefix):
                funcargfuncs.append(getattr(plugin, name))
        if not funcargfuncs:
            return
        for func in funcargfuncs:
            argname = func.__name__[len(prefix):]
            self.Print()
            self.Print(".. _`%s funcarg`:" % argname)
            self.Print()
            self.h2("the %r test function argument" % argname)
            if func.__doc__:
                doclines = func.__doc__.split("\n")
                source = py.code.Source("\n".join(doclines[1:]))
                source.lines.insert(0, doclines[0])
                self.para(str(source))
            else:
                self.para("XXX missing docstring")
                warn("missing docstring", func)

    def emit_options(self, plugin):
        from py._test.parseopt import Parser
        options = []
        parser = Parser(processopt=options.append)
        if hasattr(plugin, 'pytest_addoption'):
            plugin.pytest_addoption(parser)
        if not options:
            return
        self.h2("command line options")
        self.Print()
        formatter = py.std.optparse.IndentedHelpFormatter()
        for opt in options:
            switches = formatter.format_option_strings(opt)
            self.Print("``%s``" % switches)
            self.Print(opt.help, indent=4)

if __name__ == "__main__":
    if os.path.exists("py"):
        sys.path.insert(0, os.getcwd())
    import py
    _config = py.test.config
    _config.parse([])
    _config.pluginmanager.do_configure(_config)

    pydir = py.path.local(py.__file__).dirpath()
    pyversion = py.version

    cmd = "hg tip --template '{node}'" 
    old = pydir.dirpath().chdir()
    _config.hg_changeset = py.process.cmdexec(cmd).strip()

    testdir = pydir.dirpath("doc", 'test')
   
    ov = PluginOverview(testdir.join("plugin", "index.txt"))
    ov.make(config=_config)
    
    ov = HookSpec(testdir.join("plugin", "hookspec.txt"))
    ov.make(config=_config)

    RestWriter.write_all_links(testdir.join("plugin", "links.txt"))

