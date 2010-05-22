"""
py.test and pylib: rapid testing and development utils

this module uses apipkg.py for lazy-loading sub modules
and classes.  The initpkg-dictionary  below specifies
name->value mappings where value can be another namespace
dictionary or an import path.  

(c) Holger Krekel and others, 2004-2010
"""
__version__ = version = "1.3.1"

import py.apipkg

py.apipkg.initpkg(__name__, dict(
    # access to all standard lib modules
    std = '._std:std',
    # access to all posix errno's as classes
    error = '._error:error',

    _pydir = '.__metainfo:pydir',
    version = 'py:__version__', # backward compatibility

    cmdline = {
        'pytest':     '._cmdline.pytest:main',
        'pylookup':   '._cmdline.pylookup:main',
        'pycountloc': '._cmdline.pycountlog:main',
        'pylookup':   '._cmdline.pylookup:main',
        'pycountloc': '._cmdline.pycountloc:main',
        'pycleanup':  '._cmdline.pycleanup:main',
        'pywhich'        : '._cmdline.pywhich:main',
        'pysvnwcrevert'  : '._cmdline.pysvnwcrevert:main',
        'pyconvert_unittest'  : '._cmdline.pyconvert_unittest:main',
    },

    test = {
        # helpers for use from test functions or collectors
        '__onfirstaccess__' : '._test.config:onpytestaccess',
        '__doc__'           : '._test:__doc__',
        # configuration/initialization related test api
        'config'            : '._test.config:config_per_process',
        'ensuretemp'        : '._test.config:ensuretemp',
        'collect': {
            'Collector' : '._test.collect:Collector',
            'Directory' : '._test.collect:Directory',
            'File'      : '._test.collect:File',
            'Item'      : '._test.collect:Item',
            'Module'    : '._test.pycollect:Module',
            'Class'     : '._test.pycollect:Class',
            'Instance'  : '._test.pycollect:Instance',
            'Generator' : '._test.pycollect:Generator',
            'Function'  : '._test.pycollect:Function',
            '_fillfuncargs' : '._test.funcargs:fillfuncargs',
        },
        'cmdline': {
            'main' : '._test.cmdline:main', # backward compat
        },
    },

    # hook into the top-level standard library
    process = {
        '__doc__'        : '._process:__doc__',
        'cmdexec'        : '._process.cmdexec:cmdexec',
        'kill'           : '._process.killproc:kill',
        'ForkedFunc'     : '._process.forkedfunc:ForkedFunc',
    },

    path = {
        '__doc__'        : '._path:__doc__',
        'svnwc'          : '._path.svnwc:SvnWCCommandPath',
        'svnurl'         : '._path.svnurl:SvnCommandPath',
        'local'          : '._path.local:LocalPath',
        'SvnAuth'        : '._path.svnwc:SvnAuth',
    },

    # some nice slightly magic APIs
    magic = {
        'invoke'           : '._code.oldmagic:invoke',
        'revoke'           : '._code.oldmagic:revoke',
        'patch'            : '._code.oldmagic:patch',
        'revert'           : '._code.oldmagic:revert',
        'autopath'         : '._path.local:autopath',
        'AssertionError'   : '._code.oldmagic2:AssertionError',
    },

    # python inspection/code-generation API
    code = {
        '__doc__'           : '._code:__doc__',
        'compile'           : '._code.source:compile_',
        'Source'            : '._code.source:Source',
        'Code'              : '._code.code:Code',
        'Frame'             : '._code.code:Frame',
        'ExceptionInfo'     : '._code.code:ExceptionInfo',
        'Traceback'         : '._code.code:Traceback',
        'getfslineno'       : '._code.source:getfslineno',
        'getrawcode'        : '._code.code:getrawcode',
        'patch_builtins'    : '._code.code:patch_builtins',
        'unpatch_builtins'  : '._code.code:unpatch_builtins',
        '_AssertionError'   : '._code.assertion:AssertionError',
        '_reinterpret_old'  : '._code.assertion:reinterpret_old',
        '_reinterpret'      : '._code.assertion:reinterpret',
    },

    # backports and additions of builtins
    builtin = {
        '__doc__'        : '._builtin:__doc__',
        'enumerate'      : '._builtin:enumerate',
        'reversed'       : '._builtin:reversed',
        'sorted'         : '._builtin:sorted',
        'set'            : '._builtin:set',
        'frozenset'      : '._builtin:frozenset',
        'BaseException'  : '._builtin:BaseException',
        'GeneratorExit'  : '._builtin:GeneratorExit',
        'print_'         : '._builtin:print_',
        '_reraise'       : '._builtin:_reraise',
        '_tryimport'     : '._builtin:_tryimport',
        'exec_'          : '._builtin:exec_',
        '_basestring'    : '._builtin:_basestring',
        '_totext'        : '._builtin:_totext',
        '_isbytes'       : '._builtin:_isbytes',
        '_istext'        : '._builtin:_istext',
        '_getimself'     : '._builtin:_getimself',
        '_getfuncdict'   : '._builtin:_getfuncdict',
        '_getcode'       : '._builtin:_getcode',
        'builtins'       : '._builtin:builtins',
        'execfile'       : '._builtin:execfile',
        'callable'       : '._builtin:callable',
    },

    # input-output helping
    io = {
        '__doc__'             : '._io:__doc__',
        'dupfile'             : '._io.capture:dupfile',
        'TextIO'              : '._io.capture:TextIO',
        'BytesIO'             : '._io.capture:BytesIO',
        'FDCapture'           : '._io.capture:FDCapture',
        'StdCapture'          : '._io.capture:StdCapture',
        'StdCaptureFD'        : '._io.capture:StdCaptureFD',
        'TerminalWriter'      : '._io.terminalwriter:TerminalWriter',
        'ansi_print'          : '._io.terminalwriter:ansi_print', 
        'get_terminal_width'  : '._io.terminalwriter:get_terminal_width',
        'saferepr'            : '._io.saferepr:saferepr',
    },

    # small and mean xml/html generation
    xml = {
        '__doc__'            : '._xmlgen:__doc__',
        'html'               : '._xmlgen:html',
        'Tag'                : '._xmlgen:Tag',
        'raw'                : '._xmlgen:raw',
        'Namespace'          : '._xmlgen:Namespace',
        'escape'             : '._xmlgen:escape',
    },

    log = {
        # logging API ('producers' and 'consumers' connected via keywords)
        '__doc__'            : '._log:__doc__',
        '_apiwarn'           : '._log.warning:_apiwarn',
        'Producer'           : '._log.log:Producer',
        'setconsumer'        : '._log.log:setconsumer',
        '_setstate'          : '._log.log:setstate',
        '_getstate'          : '._log.log:getstate',
        'Path'               : '._log.log:Path',
        'STDOUT'             : '._log.log:STDOUT',
        'STDERR'             : '._log.log:STDERR',
        'Syslog'             : '._log.log:Syslog',
    },

    # compatibility modules (deprecated)
    compat = {
        '__doc__'         : '._compat:__doc__',
        'doctest'         : '._compat.dep_doctest:doctest',
        'optparse'        : '._compat.dep_optparse:optparse',
        'textwrap'        : '._compat.dep_textwrap:textwrap',
        'subprocess'      : '._compat.dep_subprocess:subprocess',
    },
))
