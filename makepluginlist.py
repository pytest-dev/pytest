
import py
import sys
WIDTH = 75

plugins = [
    ('Plugins related to Python test functions and programs', 
            'xfail figleaf monkeypatch iocapture recwarn',),
    ('Plugins for other testing styles and languages', 
            'unittest doctest restdoc osjskit'),
    ('Plugins for generic reporting and failure logging', 
            'pocoo resultlog terminal',),
    ('internal plugins / core functionality', 
        'pdb keyword hooklog runner execnetcleanup pytester',
    )
]

externals = {
    'osjskit': ('`pytest_oejskit`_ Testing Javascript in real browsers', 
    '''
jskit contains infrastructure and in particular a py.test plugin to enable running tests for JavaScript code inside browsers directly using py.test as the test driver. Running inside the browsers comes with some speed cost, on the other hand it means for example the code is tested against the real-word DOM implementations.

The approach also enables to write integration tests such that the JavaScript code is tested against server-side Python code mocked as necessary. Any server-side framework that can already be exposed through WSGI (or for which a subset of WSGI can be written to accommodate the jskit own needs) can play along.

jskit also contains code to help modularizing JavaScript code which can be used to describe and track dependencies dynamically during development and that can help resolving them statically when deploying/packaging.

jskit depends on simplejson. It also uses MochiKit - of which it ships a version within itself for convenience - for its own working though in does not imposes its usage on tested code.

jskit was initially developed by Open End AB and is released under the MIT license.
''', 'http://pypi.python.org/pypi/oejskit',
('pytest_oejskit', 
'http://bitbucket.org/pedronis/js-infrastructure/src/tip/pytest_jstests.py',
))}
                
class ExternalDoc:
    def __init__(self, name):
        self.title, self.longdesc, self.url, sourcelink = externals[name]
        self.sourcelink = sourcelink 
        
        

class PluginDoc:
    def __init__(self, plugin):
        self.plugin = plugin
        doc = plugin.__doc__.strip()
        i = doc.find("\n")
        if i == -1:
            title = doc
            longdesc = "XXX no long description available"
        else:
            title = doc[:i].strip()
            longdesc = doc[i+1:].strip()
        purename = plugin.__name__.split(".")[-1].strip()
        self.title = "`%s`_ %s" %(purename, title)
        self.longdesc = longdesc
        self.sourcelink = (purename, 
            "http://bitbucket.org/hpk42/py-trunk/src/tip/py/test/plugin/" + 
            purename + ".py")
   
def warn(msg):
    print >>sys.stderr, "WARNING:", msg

 
def makedoc(name):
    if name in externals:
        return ExternalDoc(name)
    config.pluginmanager.import_plugin(name)
    plugin = config.pluginmanager.getplugin(name)
    if plugin is None:
        return None
    return PluginDoc(plugin)

def header():
    #print "=" * WIDTH
    #print "list of available py.test plugins" 
    #print "=" * WIDTH
    print

if __name__ == "__main__":
    config = py.test.config
    config.parse([])
    config.pluginmanager.do_configure(config)

    header()
   
    links = []
    for cat, specs in plugins:
        pluginlist = specs.split()
        print len(cat) * "="
        print cat
        print len(cat) * "="
        for name in pluginlist:
            doc = makedoc(name)
            if doc is None:
                warn("skipping", name)
                continue
            print "* " + str(doc.title)
            #print len(doc.title) * "*"
            #print doc.longdesc 
            links.append(doc.sourcelink)
            print
        print 
    print
    for link in links:
        warn(repr(link))
        print ".. _`%s`: %s" % (link[0], link[1])
