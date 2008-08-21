"""
A utility to build a Python extension module from C, wrapping distutils.
"""
import py

# set to true for automatic re-compilation of extensions
AUTOREGEN = True

#  XXX we should distutils in a subprocess, because it messes up the
#      environment and who knows what else.  Currently we just save
#      and restore os.environ.

def make_module_from_c(cfile):
    import os, sys, imp
    from distutils.core import setup
    from distutils.extension import Extension
    debug = 0

    #try:
    #    from distutils.log import set_threshold
    #    set_threshold(10000)
    #except ImportError:
    #    print "ERROR IMPORTING"
    #    pass

    dirpath = cfile.dirpath()
    modname = cfile.purebasename

    # find the expected extension of the compiled C module
    for ext, mode, filetype in imp.get_suffixes():
        if filetype == imp.C_EXTENSION:
            break
    else:
        raise ImportError, "cannot find the file name suffix of C ext modules"
    lib = dirpath.join(modname+ext)

    # XXX argl! we need better "build"-locations alltogether!
    if lib.check() and AUTOREGEN and lib.stat().mtime < cfile.stat().mtime:
        try:
            lib.remove()
        except EnvironmentError:
            pass # XXX we just use the existing version, bah

    if not lib.check():
        c = py.io.StdCaptureFD()
        try:
            try:
                saved_environ = os.environ.items()
                try:
                    lastdir = dirpath.chdir()
                    try:
                        setup(
                          name = "pylibmodules",
                          ext_modules=[
                                Extension(modname, [str(cfile)])
                          ],
                          script_name = 'setup.py',
                          script_args = ['-q', 'build_ext', '--inplace']
                          #script_args = ['build_ext', '--inplace']
                        )
                    finally:
                        lastdir.chdir()
                finally:
                    for key, value in saved_environ:
                        if os.environ.get(key) != value:
                            os.environ[key] = value
            finally:
                foutput, foutput = c.done()
        except KeyboardInterrupt:
            raise
        except SystemExit, e:
            raise RuntimeError("cannot compile %s: %s\n%s" % (cfile, e,
                                                          foutput.read()))
    # XXX do we need to do some check on fout/ferr?
    # XXX not a nice way to import a module
    if debug:
        print "inserting path to sys.path", dirpath
    sys.path.insert(0, str(dirpath))
    if debug:
        print "import %(modname)s as testmodule" % locals()
    exec py.code.compile("import %(modname)s as testmodule" % locals())
    try:
        sys.path.remove(str(dirpath))
    except ValueError:
        pass

    return testmodule
