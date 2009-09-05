
# -*- coding: utf-8 -*-
"""
advanced testing and development support library: 

- `py.test`_: cross-project testing tool with many advanced features
- `py.execnet`_: ad-hoc code distribution to SSH, Socket and local sub processes
- `py.path`_: path abstractions over local and subversion files 
- `py.code`_: dynamic code compile and traceback printing support

Compatibility: Linux, Win32, OSX, Python versions 2.3-2.6. 
For questions please check out http://pylib.org/contact.html

.. _`py.test`: http://pylib.org/test.html
.. _`py.execnet`: http://pylib.org/execnet.html
.. _`py.path`: http://pylib.org/path.html
.. _`py.code`: http://pylib.org/code.html

(c) Holger Krekel and others, 2009  
"""
from py.initpkg import initpkg
trunk = "trunk"

version = trunk or "1.0.x"

del trunk 

initpkg(__name__,
    description = "py.test and pylib: advanced testing tool and networking lib", 
    version = version, 
    url = "http://pylib.org", 
    license = "MIT license",
    platforms = ['unix', 'linux', 'osx', 'cygwin', 'win32'],
    author = "holger krekel, Guido Wesdorp, Carl Friedrich Bolz, Armin Rigo, Maciej Fijalkowski & others",
    author_email = "holger at merlinux.eu, py-dev at codespeak.net",
    long_description = globals()['__doc__'],
    classifiers = [
        "Development Status :: 5 - Production/Stable", 
        "Intended Audience :: Developers", 
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Topic :: Software Development :: Testing", 
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Distributed Computing",
        "Topic :: Utilities",
        "Programming Language :: Python",
    ],

    # EXPORTED API 
    exportdefs = {

    # py lib events and plugins 
    '_com.Registry'          : ('./_com.py', 'Registry'), 
    '_com.MultiCall'         : ('./_com.py', 'MultiCall'), 
    '_com.comregistry'       : ('./_com.py', 'comregistry'), 
    '_com.HookRelay'             : ('./_com.py', 'HookRelay'), 

    # py lib cmdline tools 
    'cmdline.pytest'         : ('./cmdline/pytest.py', 'main',),
    'cmdline.pyrest'         : ('./cmdline/pyrest.py', 'main',),
    'cmdline.pylookup'       : ('./cmdline/pylookup.py', 'main',),
    'cmdline.pycountloc'     : ('./cmdline/pycountloc.py', 'main',),
    'cmdline.pycleanup'      : ('./cmdline/pycleanup.py', 'main',),
    'cmdline.pywhich'        : ('./cmdline/pywhich.py', 'main',),
    'cmdline.pysvnwcrevert'  : ('./cmdline/pysvnwcrevert.py', 'main',),
    'cmdline.pyconvert_unittest'  : ('./cmdline/pyconvert_unittest.py', 'main',),

    # helpers for use from test functions or collectors
    'test.__doc__'           : ('./test/__init__.py', '__doc__'),
    'test._PluginManager'    : ('./test/pluginmanager.py', 'PluginManager'),
    'test.raises'            : ('./test/outcome.py', 'raises'),
    'test.skip'              : ('./test/outcome.py', 'skip'),
    'test.importorskip'      : ('./test/outcome.py', 'importorskip'),
    'test.fail'              : ('./test/outcome.py', 'fail'),
    'test.exit'              : ('./test/outcome.py', 'exit'),

    # configuration/initialization related test api
    'test.config'            : ('./test/config.py', 'config_per_process'),
    'test.ensuretemp'        : ('./test/config.py', 'ensuretemp'),
    'test.cmdline.main'      : ('./test/cmdline.py', 'main'),

    # for customization of collecting/running tests
    'test.collect.Collector' : ('./test/collect.py', 'Collector'),
    'test.collect.Directory' : ('./test/collect.py', 'Directory'),
    'test.collect.File'      : ('./test/collect.py', 'File'),
    'test.collect.Item'      : ('./test/collect.py', 'Item'),
    'test.collect.Module'    : ('./test/pycollect.py', 'Module'),
    'test.collect.Class'     : ('./test/pycollect.py', 'Class'),
    'test.collect.Instance'  : ('./test/pycollect.py', 'Instance'),
    'test.collect.Generator' : ('./test/pycollect.py', 'Generator'),
    'test.collect.Function'  : ('./test/pycollect.py', 'Function'),
    'test.collect._fillfuncargs' : ('./test/funcargs.py', 'fillfuncargs'),

    # thread related API (still in early design phase)
    '_thread.WorkerPool'      : ('./thread/pool.py', 'WorkerPool'),
    '_thread.NamedThreadPool' : ('./thread/pool.py', 'NamedThreadPool'),
    '_thread.ThreadOut'       : ('./thread/io.py', 'ThreadOut'),

    # hook into the top-level standard library
    'std'                    : ('./std.py', 'std'),

    'process.__doc__'        : ('./process/__init__.py', '__doc__'),
    'process.cmdexec'        : ('./process/cmdexec.py', 'cmdexec'),
    'process.kill'           : ('./process/killproc.py', 'kill'),
    'process.ForkedFunc'     : ('./process/forkedfunc.py', 'ForkedFunc'), 

    # path implementation
    'path.__doc__'           : ('./path/__init__.py', '__doc__'),
    'path.svnwc'             : ('./path/svnwc.py', 'SvnWCCommandPath'),
    'path.svnurl'            : ('./path/svnurl.py', 'SvnCommandPath'),
    'path.local'             : ('./path/local.py', 'LocalPath'),
    'path.SvnAuth'           : ('./path/svnwc.py', 'SvnAuth'),

    # some nice slightly magic APIs
    #'magic.__doc__'          : ('./magic/__init__.py', '__doc__'),
    'magic.invoke'           : ('./code/oldmagic.py', 'invoke'),
    'magic.revoke'           : ('./code/oldmagic.py', 'revoke'),
    'magic.patch'            : ('./code/oldmagic.py', 'patch'),
    'magic.revert'           : ('./code/oldmagic.py', 'revert'),
    'magic.autopath'         : ('./path/local.py', 'autopath'),
    'magic.AssertionError'   : ('./code/oldmagic2.py', 'AssertionError'),

    # python inspection/code-generation API
    'code.__doc__'           : ('./code/__init__.py', '__doc__'),
    'code.compile'           : ('./code/source.py', 'compile_'),
    'code.Source'            : ('./code/source.py', 'Source'),
    'code.Code'              : ('./code/code.py', 'Code'),
    'code.Frame'             : ('./code/code.py', 'Frame'),
    'code.ExceptionInfo'     : ('./code/code.py', 'ExceptionInfo'),
    'code.Traceback'         : ('./code/code.py', 'Traceback'),
    'code.getfslineno'       : ('./code/source.py', 'getfslineno'),
    'code.getrawcode'        : ('./code/code.py', 'getrawcode'),
    'code.patch_builtins'    : ('./code/code.py', 'patch_builtins'),
    'code.unpatch_builtins'  : ('./code/code.py', 'unpatch_builtins'),
    'code._AssertionError'   : ('./code/assertion.py', 'AssertionError'),

    # backports and additions of builtins
    'builtin.__doc__'        : ('./builtin/__init__.py', '__doc__'),
    'builtin.enumerate'      : ('./builtin/builtin24.py', 'enumerate'),
    'builtin.reversed'       : ('./builtin/builtin24.py', 'reversed'),
    'builtin.sorted'         : ('./builtin/builtin24.py', 'sorted'),
    'builtin.set'            : ('./builtin/builtin24.py', 'set'),
    'builtin.frozenset'      : ('./builtin/builtin24.py', 'frozenset'),
    'builtin.BaseException'  : ('./builtin/builtin25.py', 'BaseException'),
    'builtin.GeneratorExit'  : ('./builtin/builtin25.py', 'GeneratorExit'),
    'builtin.print_'         : ('./builtin/builtin31.py', 'print_'),
    'builtin._reraise'       : ('./builtin/builtin31.py', '_reraise'),
    'builtin._tryimport'     : ('./builtin/builtin31.py', '_tryimport'),
    'builtin.exec_'          : ('./builtin/builtin31.py', 'exec_'),
    'builtin._basestring'    : ('./builtin/builtin31.py', '_basestring'),
    'builtin._totext'        : ('./builtin/builtin31.py', '_totext'),
    'builtin._isbytes'       : ('./builtin/builtin31.py', '_isbytes'),
    'builtin._istext'        : ('./builtin/builtin31.py', '_istext'),
    'builtin._getimself'     : ('./builtin/builtin31.py', '_getimself'),
    'builtin._getfuncdict'   : ('./builtin/builtin31.py', '_getfuncdict'),
    'builtin.builtins'       : ('./builtin/builtin31.py', 'builtins'),
    'builtin.execfile'       : ('./builtin/builtin31.py', 'execfile'),
    'builtin.callable'       : ('./builtin/builtin31.py', 'callable'),

    # gateways into remote contexts
    'execnet.__doc__'        : ('./execnet/__init__.py', '__doc__'),
    'execnet._HookSpecs'     : ('./execnet/gateway_base.py', 'ExecnetAPI'),
    'execnet.SocketGateway'  : ('./execnet/gateway.py', 'SocketGateway'),
    'execnet.PopenGateway'   : ('./execnet/gateway.py', 'PopenGateway'),
    'execnet.SshGateway'     : ('./execnet/gateway.py', 'SshGateway'),
    'execnet.XSpec'          : ('./execnet/xspec.py', 'XSpec'),
    'execnet.makegateway'    : ('./execnet/xspec.py', 'makegateway'),
    'execnet.MultiGateway'   : ('./execnet/multi.py', 'MultiGateway'),
    'execnet.MultiChannel'   : ('./execnet/multi.py', 'MultiChannel'),

    # execnet scripts
    'execnet.RSync'          : ('./execnet/rsync.py', 'RSync'),

    # input-output helping 
    'io.__doc__'             : ('./io/__init__.py', '__doc__'),
    'io.dupfile'             : ('./io/capture.py', 'dupfile'), 
    'io.TextIO'              : ('./io/capture.py', 'TextIO'), 
    'io.BytesIO'             : ('./io/capture.py', 'BytesIO'), 
    'io.FDCapture'           : ('./io/capture.py', 'FDCapture'), 
    'io.StdCapture'          : ('./io/capture.py', 'StdCapture'), 
    'io.StdCaptureFD'        : ('./io/capture.py', 'StdCaptureFD'), 
    'io.TerminalWriter'      : ('./io/terminalwriter.py', 'TerminalWriter'), 

    # error module, defining all errno's as Classes
    'error'                  : ('./error.py', 'error'),

    # small and mean xml/html generation
    'xml.__doc__'            : ('./xmlgen.py', '__doc__'), 
    'xml.html'               : ('./xmlgen.py', 'html'),
    'xml.Tag'                : ('./xmlgen.py', 'Tag'),
    'xml.raw'                : ('./xmlgen.py', 'raw'),
    'xml.Namespace'          : ('./xmlgen.py', 'Namespace'),
    'xml.escape'             : ('./xmlgen.py', 'escape'),

    # logging API ('producers' and 'consumers' connected via keywords)
    'log.__doc__'            : ('./log/__init__.py', '__doc__'),
    'log._apiwarn'           : ('./log/warning.py', '_apiwarn'),
    'log.Producer'           : ('./log/log.py', 'Producer'),
    'log.setconsumer'        : ('./log/log.py', 'setconsumer'),
    'log._setstate'          : ('./log/log.py', 'setstate'),
    'log._getstate'          : ('./log/log.py', 'getstate'),
    'log.Path'               : ('./log/log.py', 'Path'),
    'log.STDOUT'             : ('./log/log.py', 'STDOUT'),
    'log.STDERR'             : ('./log/log.py', 'STDERR'),
    'log.Syslog'             : ('./log/log.py', 'Syslog'),

    # compatibility modules (deprecated)
    'compat.__doc__'         : ('./compat/__init__.py', '__doc__'),
    'compat.doctest'         : ('./compat/dep_doctest.py', 'doctest'),
    'compat.optparse'        : ('./compat/dep_optparse.py', 'optparse'),
    'compat.textwrap'        : ('./compat/dep_textwrap.py', 'textwrap'),
    'compat.subprocess'      : ('./compat/dep_subprocess.py', 'subprocess'),
})



