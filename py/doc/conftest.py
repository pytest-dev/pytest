from __future__ import generators
import py
from py.__.misc import rest 

Option = py.test.config.Option 
option = py.test.config.addoptions("documentation check options", 
        Option('-R', '--checkremote',
               action="store_true", dest="checkremote", default=False,
               help="check remote links in ReST files"
        ),
        Option('', '--forcegen',
               action="store_true", dest="forcegen", default=False,
               help="force generation of html files even if they appear up-to-date"
        )
) 

_initialized = False
def checkdocutils():
    global _initialized
    try:
        import docutils
    except ImportError:
        py.test.skip("docutils not importable")
    if not _initialized:
        from py.__.rest import directive
        directive.register_linkrole('api', resolve_linkrole)
        directive.register_linkrole('source', resolve_linkrole)
        _initialized = True

def restcheck(path):
    localpath = path
    if hasattr(path, 'localpath'):
        localpath = path.localpath
    _checkskip(localpath)
    checkdocutils() 
    import docutils.utils

    try: 
        cur = localpath
        for x in cur.parts(reverse=True):
            confrest = x.dirpath('confrest.py')
            if confrest.check(file=1): 
                confrest = confrest.pyimport() 
                confrest.Project().process(path) 
                break
        else: 
            # defer to default processor 
            rest.process(path) 
    except KeyboardInterrupt: 
        raise 
    except docutils.utils.SystemMessage: 
        # we assume docutils printed info on stdout 
        py.test.fail("docutils processing failed, see captured stderr") 

def _checkskip(lpath):
    if not option.forcegen:
        if lpath.ext == '.txt': 
            htmlpath = lpath.new(ext='.html')
            if htmlpath.check(file=1) and htmlpath.mtime() >= lpath.mtime(): 
                py.test.skip("html file is up to date, use --forcegen to regenerate")
                #return [] # no need to rebuild 

class ReSTSyntaxTest(py.test.Item): 
    def run(self):
        mypath = self.fspath 
        _checkskip(mypath)
        restcheck(py.path.svnwc(mypath))

class DoctestText(py.test.Item): 
    def run(self): 
        # XXX quite nasty... but it works (fixes win32 issues)
        s = self._normalize_linesep()
        l = []
        prefix = '.. >>> '
        mod = py.std.types.ModuleType(self.fspath.purebasename) 
        for line in s.split('\n'):
            line = line.strip()
            if line.startswith(prefix):
                exec py.code.Source(line[len(prefix):]).compile() in \
                     mod.__dict__
                line = ""
            else:
                l.append(line)
        docstring = "\n".join(l)
        self.execute(mod, docstring)

    def execute(self, mod, docstring): 
        mod.__doc__ = docstring 
        failed, tot = py.compat.doctest.testmod(mod, verbose=1)
        if failed: 
            py.test.fail("doctest %s: %s failed out of %s" %(
                         self.fspath, failed, tot))

    def _normalize_linesep(self):
        s = self.fspath.read()
        linesep = '\n'
        if '\r' in s:
            if '\n' not in s:
                linesep = '\r'
            else:
                linesep = '\r\n'
        s = s.replace(linesep, '\n')
        return s
        
class LinkCheckerMaker(py.test.collect.Collector): 
    def run(self): 
        l = []
        for call, tryfn, path, lineno in genlinkchecks(self.fspath): 
            l.append(tryfn) 
        return l
        
    def join(self, name): 
        for call, tryfn, path, lineno in genlinkchecks(self.fspath): 
            if tryfn == name: 
                return CheckLink(name, parent=self, args=(tryfn, path, lineno), obj=call)
      
class CheckLink(py.test.Function): 
    def setup(self): 
        pass 
    def teardown(self): 
        pass 

class ReSTChecker(py.test.collect.Module): 
    DoctestText = DoctestText
    ReSTSyntaxTest = ReSTSyntaxTest
    
    def __repr__(self): 
        return py.test.collect.Collector.__repr__(self) 

    def setup(self): 
        pass 
    def teardown(self): 
        pass 
    def run(self):
        return [self.fspath.basename, 'checklinks', 'doctest']
    def join(self, name): 
        if name == self.fspath.basename: 
            return self.ReSTSyntaxTest(name, parent=self) 
        elif name == 'checklinks': 
            return LinkCheckerMaker(name, self) 
        elif name == 'doctest': 
            return self.DoctestText(name, self) 

# generating functions + args as single tests 
def genlinkchecks(path): 
    for lineno, line in py.builtin.enumerate(path.readlines()): 
        line = line.strip()
        if line.startswith('.. _'): 
            if line.startswith('.. _`'):
                delim = '`:'
            else:
                delim = ':'
            l = line.split(delim, 1)
            if len(l) != 2: 
                continue
            tryfn = l[1].strip() 
            if tryfn.startswith('http:') or tryfn.startswith('https'): 
                if option.checkremote: 
                    yield urlcheck, tryfn, path, lineno 
            elif tryfn.startswith('webcal:'):
                continue
            else: 
                i = tryfn.find('#') 
                if i != -1: 
                    checkfn = tryfn[:i]
                else: 
                    checkfn = tryfn 
                if checkfn.strip() and (1 or checkfn.endswith('.html')): 
                    yield localrefcheck, tryfn, path, lineno 

def urlcheck(tryfn, path, lineno): 
    try: 
        print "trying remote", tryfn
        py.std.urllib2.urlopen(tryfn)
    except (py.std.urllib2.URLError, py.std.urllib2.HTTPError), e: 
        if e.code in (401, 403): # authorization required, forbidden
            py.test.skip("%s: %s" %(tryfn, str(e)))
        else:
            py.test.fail("remote reference error %r in %s:%d\n%s" %(
                         tryfn, path.basename, lineno+1, e))

def localrefcheck(tryfn, path, lineno): 
    # assume it should be a file 
    i = tryfn.find('#')
    if tryfn.startswith('javascript:'):
        return # don't check JS refs
    if i != -1: 
        anchor = tryfn[i+1:]
        tryfn = tryfn[:i]
    else: 
        anchor = ''
    fn = path.dirpath(tryfn) 
    ishtml = fn.ext == '.html' 
    fn = ishtml and fn.new(ext='.txt') or fn
    print "filename is", fn 
    if not fn.check(): # not ishtml or not fn.check(): 
        py.test.fail("reference error %r in %s:%d" %(
                      tryfn, path.basename, lineno+1))
    if anchor: 
        source = unicode(fn.read(), 'latin1')
        source = source.lower().replace('-', ' ') # aehem

        anchor = anchor.replace('-', ' ') 
        match2 = ".. _`%s`:" % anchor 
        match3 = ".. _%s:" % anchor 
        candidates = (anchor, match2, match3)
        print "candidates", repr(candidates)
        for line in source.split('\n'): 
            line = line.strip()
            if line in candidates: 
                break 
        else: 
            py.test.fail("anchor reference error %s#%s in %s:%d" %(
                tryfn, anchor, path.basename, lineno+1))


# ___________________________________________________________
# 
# hooking into py.test Directory collector's chain ... 

class DocDirectory(py.test.collect.Directory): 
    ReSTChecker = ReSTChecker 

    def run(self): 
        results = super(DocDirectory, self).run() 
        for x in self.fspath.listdir('*.txt', sort=True): 
            results.append(x.basename) 
        return results 

    def join(self, name): 
        if not name.endswith('.txt'): 
            return super(DocDirectory, self).join(name) 
        p = self.fspath.join(name) 
        if p.check(file=1): 
            return self.ReSTChecker(p, parent=self) 
Directory = DocDirectory

def resolve_linkrole(name, text, check=True):
    if name == 'api':
        if text == 'py':
            return ('py', '../../apigen/api/index.html')
        else:
            assert text.startswith('py.'), (
                'api link "%s" does not point to the py package') % (text,)
            dotted_name = text
            if dotted_name.find('(') > -1:
                dotted_name = dotted_name[:text.find('(')]
            # remove pkg root
            path = dotted_name.split('.')[1:]
            dotted_name = '.'.join(path)
            obj = py
            if check:
                for chunk in path:
                    try:
                        obj = getattr(obj, chunk)
                    except AttributeError:
                        raise AssertionError(
                            'problem with linkrole :api:`%s`: can not resolve '
                            'dotted name %s' % (text, dotted_name,))
            return (text, '../../apigen/api/%s.html' % (dotted_name,))
    elif name == 'source':
        assert text.startswith('py/'), ('source link "%s" does not point '
                                        'to the py package') % (text,)
        relpath = '/'.join(text.split('/')[1:])
        if check:
            pkgroot = py.__package__.getpath()
            abspath = pkgroot.join(relpath)
            assert pkgroot.join(relpath).check(), (
                    'problem with linkrole :source:`%s`: '
                    'path %s does not exist' % (text, relpath))
        if relpath.endswith('/') or not relpath:
            relpath += 'index.html'
        else:
            relpath += '.html'
        return (text, '../../apigen/source/%s' % (relpath,))

