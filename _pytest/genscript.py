""" generate a single-file self-contained version of py.test """
import py

def find_toplevel(name):
    for syspath in py.std.sys.path:
        base = py.path.local(syspath)
        lib = base/name
        if lib.check(dir=1):
            return lib
        mod = base.join("%s.py" % name)
        if mod.check(file=1):
            return mod
    raise LookupError(name)

def pkgname(toplevel, rootpath, path):
    parts = path.parts()[len(rootpath.parts()):]
    return '.'.join([toplevel] + [x.purebasename for x in parts])

def pkg_to_mapping(name):
    toplevel = find_toplevel(name)
    name2src = {}
    if toplevel.check(file=1): # module
        name2src[toplevel.purebasename] = toplevel.read()
    else: # package
        for pyfile in toplevel.visit('*.py'):
            pkg = pkgname(name, toplevel, pyfile)
            name2src[pkg] = pyfile.read()
    return name2src

def compress_mapping(mapping):
    data = py.std.pickle.dumps(mapping, 2)
    data = py.std.zlib.compress(data, 9)
    data = py.std.base64.encodestring(data)
    data = data.decode('ascii')
    return data


def compress_packages(names):
    mapping = {}
    for name in names:
        mapping.update(pkg_to_mapping(name))
    return compress_mapping(mapping)

def generate_script(entry, packages):
    data = compress_packages(packages)
    tmpl = py.path.local(__file__).dirpath().join('standalonetemplate.py')
    exe = tmpl.read()
    exe = exe.replace('@SOURCES@', data)
    exe = exe.replace('@ENTRY@', entry)
    return exe


def pytest_addoption(parser):
    group = parser.getgroup("debugconfig")
    group.addoption("--genscript", action="store", default=None,
        dest="genscript", metavar="path",
        help="create standalone py.test script at given target path.")

def pytest_cmdline_main(config):
    genscript = config.getvalue("genscript")
    if genscript:
        script = generate_script(
            'import py; raise SystemExit(py.test.cmdline.main())',
            ['py', '_pytest', 'pytest'],
        )

        genscript = py.path.local(genscript)
        genscript.write(script)
        return 0
