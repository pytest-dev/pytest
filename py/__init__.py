# -*- coding: utf-8 -*-
"""
py.test and pylib: rapid testing and development utils

this module uses apipkg.py for lazy-loading sub modules
and classes.  The initpkg-dictionary  below specifies
name->value mappings where value can be another namespace
dictionary or an import path.  

(c) Holger Krekel and others, 2009
"""
version = "1.1.1post1"

__version__ = version = version or "1.1.x"
import py.apipkg

py.apipkg.initpkg(__name__, dict(
    # access to all standard lib modules
    std = '.impl.std:std',
    # access to all posix errno's as classes
    error = '.impl.error:error',

    _impldir = '.impl._metainfo:impldir',
    _dir = '.impl._metainfo:pydir',
    _pydirs = '.impl._metainfo:pydirs',
    version = 'py:__version__', # backward compatibility

    _com = {
        'Registry': '.impl._com:Registry',
        'MultiCall':  '.impl._com:MultiCall',
        'comregistry': '.impl._com:comregistry',
        'HookRelay': '.impl._com:HookRelay',
    },
    cmdline = {
        'pytest':     '.impl.cmdline.pytest:main',
        'pylookup':   '.impl.cmdline.pylookup:main',
        'pycountloc': '.impl.cmdline.pycountlog:main',
        'pytest':     '.impl.test.cmdline:main',
        'pylookup':   '.impl.cmdline.pylookup:main',
        'pycountloc': '.impl.cmdline.pycountloc:main',
        'pycleanup':  '.impl.cmdline.pycleanup:main',
        'pywhich'        : '.impl.cmdline.pywhich:main',
        'pysvnwcrevert'  : '.impl.cmdline.pysvnwcrevert:main',
        'pyconvert_unittest'  : '.impl.cmdline.pyconvert_unittest:main',
    },

    test = {
        # helpers for use from test functions or collectors
        '__doc__'           : '.impl.test:__doc__',
        '_PluginManager'    : '.impl.test.pluginmanager:PluginManager',
        'raises'            : '.impl.test.outcome:raises',
        'skip'              : '.impl.test.outcome:skip',
        'importorskip'      : '.impl.test.outcome:importorskip',
        'fail'              : '.impl.test.outcome:fail',
        'exit'              : '.impl.test.outcome:exit',
        # configuration/initialization related test api
        'config'            : '.impl.test.config:config_per_process',
        'ensuretemp'        : '.impl.test.config:ensuretemp',
        'collect': {
            'Collector' : '.impl.test.collect:Collector',
            'Directory' : '.impl.test.collect:Directory',
            'File'      : '.impl.test.collect:File',
            'Item'      : '.impl.test.collect:Item',
            'Module'    : '.impl.test.pycollect:Module',
            'Class'     : '.impl.test.pycollect:Class',
            'Instance'  : '.impl.test.pycollect:Instance',
            'Generator' : '.impl.test.pycollect:Generator',
            'Function'  : '.impl.test.pycollect:Function',
            '_fillfuncargs' : '.impl.test.funcargs:fillfuncargs',
        },
        'cmdline': {
            'main' : '.impl.test.cmdline:main', # backward compat
        },
    },

    # hook into the top-level standard library
    process = {
        '__doc__'        : '.impl.process:__doc__',
        'cmdexec'        : '.impl.process.cmdexec:cmdexec',
        'kill'           : '.impl.process.killproc:kill',
        'ForkedFunc'     : '.impl.process.forkedfunc:ForkedFunc',
    },

    path = {
        '__doc__'        : '.impl.path:__doc__',
        'svnwc'          : '.impl.path.svnwc:SvnWCCommandPath',
        'svnurl'         : '.impl.path.svnurl:SvnCommandPath',
        'local'          : '.impl.path.local:LocalPath',
        'SvnAuth'        : '.impl.path.svnwc:SvnAuth',
    },

    # some nice slightly magic APIs
    magic = {
        'invoke'           : '.impl.code.oldmagic:invoke',
        'revoke'           : '.impl.code.oldmagic:revoke',
        'patch'            : '.impl.code.oldmagic:patch',
        'revert'           : '.impl.code.oldmagic:revert',
        'autopath'         : '.impl.path.local:autopath',
        'AssertionError'   : '.impl.code.oldmagic2:AssertionError',
    },

    # python inspection/code-generation API
    code = {
        '__doc__'           : '.impl.code:__doc__',
        'compile'           : '.impl.code.source:compile_',
        'Source'            : '.impl.code.source:Source',
        'Code'              : '.impl.code.code:Code',
        'Frame'             : '.impl.code.code:Frame',
        'ExceptionInfo'     : '.impl.code.code:ExceptionInfo',
        'Traceback'         : '.impl.code.code:Traceback',
        'getfslineno'       : '.impl.code.source:getfslineno',
        'getrawcode'        : '.impl.code.code:getrawcode',
        'patch_builtins'    : '.impl.code.code:patch_builtins',
        'unpatch_builtins'  : '.impl.code.code:unpatch_builtins',
        '_AssertionError'   : '.impl.code.assertion:AssertionError',
    },

    # backports and additions of builtins
    builtin = {
        '__doc__'        : '.impl.builtin:__doc__',
        'enumerate'      : '.impl.builtin:enumerate',
        'reversed'       : '.impl.builtin:reversed',
        'sorted'         : '.impl.builtin:sorted',
        'set'            : '.impl.builtin:set',
        'frozenset'      : '.impl.builtin:frozenset',
        'BaseException'  : '.impl.builtin:BaseException',
        'GeneratorExit'  : '.impl.builtin:GeneratorExit',
        'print_'         : '.impl.builtin:print_',
        '_reraise'       : '.impl.builtin:_reraise',
        '_tryimport'     : '.impl.builtin:_tryimport',
        'exec_'          : '.impl.builtin:exec_',
        '_basestring'    : '.impl.builtin:_basestring',
        '_totext'        : '.impl.builtin:_totext',
        '_isbytes'       : '.impl.builtin:_isbytes',
        '_istext'        : '.impl.builtin:_istext',
        '_getimself'     : '.impl.builtin:_getimself',
        '_getfuncdict'   : '.impl.builtin:_getfuncdict',
        'builtins'       : '.impl.builtin:builtins',
        'execfile'       : '.impl.builtin:execfile',
        'callable'       : '.impl.builtin:callable',
    },

    # input-output helping
    io = {
        '__doc__'             : '.impl.io:__doc__',
        'dupfile'             : '.impl.io.capture:dupfile',
        'TextIO'              : '.impl.io.capture:TextIO',
        'BytesIO'             : '.impl.io.capture:BytesIO',
        'FDCapture'           : '.impl.io.capture:FDCapture',
        'StdCapture'          : '.impl.io.capture:StdCapture',
        'StdCaptureFD'        : '.impl.io.capture:StdCaptureFD',
        'TerminalWriter'      : '.impl.io.terminalwriter:TerminalWriter',
    },

    # small and mean xml/html generation
    xml = {
        '__doc__'            : '.impl.xmlgen:__doc__',
        'html'               : '.impl.xmlgen:html',
        'Tag'                : '.impl.xmlgen:Tag',
        'raw'                : '.impl.xmlgen:raw',
        'Namespace'          : '.impl.xmlgen:Namespace',
        'escape'             : '.impl.xmlgen:escape',
    },

    log = {
        # logging API ('producers' and 'consumers' connected via keywords)
        '__doc__'            : '.impl.log:__doc__',
        '_apiwarn'           : '.impl.log.warning:_apiwarn',
        'Producer'           : '.impl.log.log:Producer',
        'setconsumer'        : '.impl.log.log:setconsumer',
        '_setstate'          : '.impl.log.log:setstate',
        '_getstate'          : '.impl.log.log:getstate',
        'Path'               : '.impl.log.log:Path',
        'STDOUT'             : '.impl.log.log:STDOUT',
        'STDERR'             : '.impl.log.log:STDERR',
        'Syslog'             : '.impl.log.log:Syslog',
    },

    # compatibility modules (deprecated)
    compat = {
        '__doc__'         : '.impl.compat:__doc__',
        'doctest'         : '.impl.compat.dep_doctest:doctest',
        'optparse'        : '.impl.compat.dep_optparse:optparse',
        'textwrap'        : '.impl.compat.dep_textwrap:textwrap',
        'subprocess'      : '.impl.compat.dep_subprocess:subprocess',
    },
))
