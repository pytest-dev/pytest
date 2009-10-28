# -*- coding: utf-8 -*-
"""
py.test and pylib: rapid testing and development utils

- `py.test`_: cross-project testing tool with many advanced features
- `py.path`_: path abstractions over local and subversion files
- `py.code`_: dynamic code compile and traceback printing support

Compatibility: Linux, Win32, OSX, Python versions 2.4 through to 3.1.
For questions please check out http://pylib.org/contact.html

.. _`py.test`: http://pylib.org/test.html
.. _`py.path`: http://pylib.org/path.html
.. _`py.code`: http://pylib.org/html

(c) Holger Krekel and others, 2009
"""
version = "trunk"

__version__ = version = version or "1.1.x"
import _py.apipkg

_py.apipkg.initpkg(__name__, dict(
    # access to all standard lib modules
    std = '_py.std:std',
    # access to all posix errno's as classes
    error = '_py.error:error',

    _impldir = '_py._metainfo:impldir',
    version = 'py:__version__', # backward compatibility

    _com = {
        'Registry': '_py._com:Registry',
        'MultiCall':  '_py._com:MultiCall',
        'comregistry': '_py._com:comregistry',
        'HookRelay': '_py._com:HookRelay',
    },
    cmdline = {
        'pytest':     '_py.cmdline.pytest:main',
        'pyrest':     '_py.cmdline.pyrest:main',
        'pylookup':   '_py.cmdline.pylookup:main',
        'pycountloc': '_py.cmdline.pycountlog:main',
        'pytest':     '_py.test.cmdline:main',
        'pyrest':     '_py.cmdline.pyrest:main',
        'pylookup':   '_py.cmdline.pylookup:main',
        'pycountloc': '_py.cmdline.pycountloc:main',
        'pycleanup':  '_py.cmdline.pycleanup:main',
        'pywhich'        : '_py.cmdline.pywhich:main',
        'pysvnwcrevert'  : '_py.cmdline.pysvnwcrevert:main',
        'pyconvert_unittest'  : '_py.cmdline.pyconvert_unittest:main',
    },

    test = {
        # helpers for use from test functions or collectors
        '__doc__'           : '_py.test:__doc__',
        '_PluginManager'    : '_py.test.pluginmanager:PluginManager',
        'raises'            : '_py.test.outcome:raises',
        'skip'              : '_py.test.outcome:skip',
        'importorskip'      : '_py.test.outcome:importorskip',
        'fail'              : '_py.test.outcome:fail',
        'exit'              : '_py.test.outcome:exit',
        # configuration/initialization related test api
        'config'            : '_py.test.config:config_per_process',
        'ensuretemp'        : '_py.test.config:ensuretemp',
        'collect': {
            'Collector' : '_py.test.collect:Collector',
            'Directory' : '_py.test.collect:Directory',
            'File'      : '_py.test.collect:File',
            'Item'      : '_py.test.collect:Item',
            'Module'    : '_py.test.pycollect:Module',
            'Class'     : '_py.test.pycollect:Class',
            'Instance'  : '_py.test.pycollect:Instance',
            'Generator' : '_py.test.pycollect:Generator',
            'Function'  : '_py.test.pycollect:Function',
            '_fillfuncargs' : '_py.test.funcargs:fillfuncargs',
        },
    },

    # hook into the top-level standard library
    process = {
        '__doc__'        : '_py.process:__doc__',
        'cmdexec'        : '_py.process.cmdexec:cmdexec',
        'kill'           : '_py.process.killproc:kill',
        'ForkedFunc'     : '_py.process.forkedfunc:ForkedFunc',
    },

    path = {
        '__doc__'        : '_py.path:__doc__',
        'svnwc'          : '_py.path.svnwc:SvnWCCommandPath',
        'svnurl'         : '_py.path.svnurl:SvnCommandPath',
        'local'          : '_py.path.local:LocalPath',
        'SvnAuth'        : '_py.path.svnwc:SvnAuth',
    },

    # some nice slightly magic APIs
    magic = {
        'invoke'           : '_py.code.oldmagic:invoke',
        'revoke'           : '_py.code.oldmagic:revoke',
        'patch'            : '_py.code.oldmagic:patch',
        'revert'           : '_py.code.oldmagic:revert',
        'autopath'         : '_py.path.local:autopath',
        'AssertionError'   : '_py.code.oldmagic2:AssertionError',
    },

    # python inspection/code-generation API
    code = {
        '__doc__'           : '_py.code:__doc__',
        'compile'           : '_py.code.source:compile_',
        'Source'            : '_py.code.source:Source',
        'Code'              : '_py.code.code:Code',
        'Frame'             : '_py.code.code:Frame',
        'ExceptionInfo'     : '_py.code.code:ExceptionInfo',
        'Traceback'         : '_py.code.code:Traceback',
        'getfslineno'       : '_py.code.source:getfslineno',
        'getrawcode'        : '_py.code.code:getrawcode',
        'patch_builtins'    : '_py.code.code:patch_builtins',
        'unpatch_builtins'  : '_py.code.code:unpatch_builtins',
        '_AssertionError'   : '_py.code.assertion:AssertionError',
    },

    # backports and additions of builtins
    builtin = {
        '__doc__'        : '_py.builtin:__doc__',
        'enumerate'      : '_py.builtin:enumerate',
        'reversed'       : '_py.builtin:reversed',
        'sorted'         : '_py.builtin:sorted',
        'set'            : '_py.builtin:set',
        'frozenset'      : '_py.builtin:frozenset',
        'BaseException'  : '_py.builtin:BaseException',
        'GeneratorExit'  : '_py.builtin:GeneratorExit',
        'print_'         : '_py.builtin:print_',
        '_reraise'       : '_py.builtin:_reraise',
        '_tryimport'     : '_py.builtin:_tryimport',
        'exec_'          : '_py.builtin:exec_',
        '_basestring'    : '_py.builtin:_basestring',
        '_totext'        : '_py.builtin:_totext',
        '_isbytes'       : '_py.builtin:_isbytes',
        '_istext'        : '_py.builtin:_istext',
        '_getimself'     : '_py.builtin:_getimself',
        '_getfuncdict'   : '_py.builtin:_getfuncdict',
        'builtins'       : '_py.builtin:builtins',
        'execfile'       : '_py.builtin:execfile',
        'callable'       : '_py.builtin:callable',
    },

    # input-output helping
    io = {
        '__doc__'             : '_py.io:__doc__',
        'dupfile'             : '_py.io.capture:dupfile',
        'TextIO'              : '_py.io.capture:TextIO',
        'BytesIO'             : '_py.io.capture:BytesIO',
        'FDCapture'           : '_py.io.capture:FDCapture',
        'StdCapture'          : '_py.io.capture:StdCapture',
        'StdCaptureFD'        : '_py.io.capture:StdCaptureFD',
        'TerminalWriter'      : '_py.io.terminalwriter:TerminalWriter',
    },

    # small and mean xml/html generation
    xml = {
        '__doc__'            : '_py.xmlgen:__doc__',
        'html'               : '_py.xmlgen:html',
        'Tag'                : '_py.xmlgen:Tag',
        'raw'                : '_py.xmlgen:raw',
        'Namespace'          : '_py.xmlgen:Namespace',
        'escape'             : '_py.xmlgen:escape',
    },

    log = {
        # logging API ('producers' and 'consumers' connected via keywords)
        '__doc__'            : '_py.log:__doc__',
        '_apiwarn'           : '_py.log.warning:_apiwarn',
        'Producer'           : '_py.log.log:Producer',
        'setconsumer'        : '_py.log.log:setconsumer',
        '_setstate'          : '_py.log.log:setstate',
        '_getstate'          : '_py.log.log:getstate',
        'Path'               : '_py.log.log:Path',
        'STDOUT'             : '_py.log.log:STDOUT',
        'STDERR'             : '_py.log.log:STDERR',
        'Syslog'             : '_py.log.log:Syslog',
    },

    # compatibility modules (deprecated)
    compat = {
        '__doc__'         : '_py.compat:__doc__',
        'doctest'         : '_py.compat.dep_doctest:doctest',
        'optparse'        : '_py.compat.dep_optparse:optparse',
        'textwrap'        : '_py.compat.dep_textwrap:textwrap',
        'subprocess'      : '_py.compat.dep_subprocess:subprocess',
    },
))
