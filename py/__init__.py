"""\
the py lib is a development support library featuring
py.test, an interactive testing tool which supports
unit-testing with practically no boilerplate.
"""
from initpkg import initpkg

version = "0.8.80-alpha2"

initpkg(__name__,
    description = "py.test and the py lib",
    revision = int('$LastChangedRevision: 37699 $'.split(':')[1][:-1]),
    lastchangedate = '$LastChangedDate: 2007-01-31 23:23:24 +0100 (Wed, 31 Jan 2007) $',
    version = version, 
    url = "http://codespeak.net/py",
    download_url = "http://codespeak.net/download/py/%s.tar.gz" %(version,), 
    license = "MIT license",
    platforms = ['unix', 'linux', 'cygwin'],
    author = "holger krekel & others",
    author_email = "py-dev@codespeak.net",
    long_description = globals()['__doc__'],

    exportdefs = {
    # helpers for use from test functions or collectors
    'test.raises'            : ('./test/raises.py', 'raises'),
    'test.deprecated_call'   : ('./test/deprecate.py', 'deprecated_call'), 
    'test.skip'              : ('./test/item.py', 'skip'),
    'test.fail'              : ('./test/item.py', 'fail'),
    'test.exit'              : ('./test/session.py', 'exit'),

    # configuration/initialization related test api
    'test.config'            : ('./test/config.py', 'config_per_process'),
    'test.ensuretemp'        : ('./test/config.py', 'ensuretemp'),
    'test.cmdline.main'      : ('./test/cmdline.py', 'main'),

    # for customization of collecting/running tests
    'test.collect.Collector' : ('./test/collect.py', 'Collector'),
    'test.collect.Directory' : ('./test/collect.py', 'Directory'),
    'test.collect.Module'    : ('./test/collect.py', 'Module'),
    'test.collect.DoctestFile' : ('./test/collect.py', 'DoctestFile'),
    'test.collect.Class'     : ('./test/collect.py', 'Class'),
    'test.collect.Instance'  : ('./test/collect.py', 'Instance'),
    'test.collect.Generator' : ('./test/collect.py', 'Generator'),
    'test.Item'              : ('./test/item.py', 'Item'),
    'test.Function'          : ('./test/item.py', 'Function'),

    # thread related API (still in early design phase)
    '_thread.WorkerPool'      : ('./thread/pool.py', 'WorkerPool'),
    '_thread.NamedThreadPool' : ('./thread/pool.py', 'NamedThreadPool'),
    '_thread.ThreadOut'       : ('./thread/io.py', 'ThreadOut'),

    # hook into the top-level standard library
    'std'                    : ('./misc/std.py', 'std'),

    'process.cmdexec'        : ('./process/cmdexec.py', 'cmdexec'),

    # path implementations
    'path.svnwc'             : ('./path/svn/wccommand.py', 'SvnWCCommandPath'),
    'path.svnurl'            : ('./path/svn/urlcommand.py', 'SvnCommandPath'),
    'path.local'             : ('./path/local/local.py', 'LocalPath'),

    # some nice slightly magic APIs
    'magic.greenlet'         : ('./magic/greenlet.py', 'greenlet'),
    'magic.invoke'           : ('./magic/invoke.py', 'invoke'),
    'magic.revoke'           : ('./magic/invoke.py', 'revoke'),
    'magic.patch'            : ('./magic/patch.py', 'patch'),
    'magic.revert'           : ('./magic/patch.py', 'revert'),
    'magic.autopath'         : ('./magic/autopath.py', 'autopath'),
    'magic.AssertionError'   : ('./magic/assertion.py', 'AssertionError'),

    # python inspection/code-generation API
    'code.compile'           : ('./code/source.py', 'compile_'),
    'code.Source'            : ('./code/source.py', 'Source'),
    'code.Code'              : ('./code/code.py', 'Code'),
    'code.Frame'             : ('./code/frame.py', 'Frame'),
    'code.ExceptionInfo'     : ('./code/excinfo.py', 'ExceptionInfo'),
    'code.Traceback'         : ('./code/traceback2.py', 'Traceback'),

    # backports and additions of builtins
    'builtin.enumerate'      : ('./builtin/enumerate.py', 'enumerate'),
    'builtin.reversed'       : ('./builtin/reversed.py',  'reversed'),
    'builtin.sorted'         : ('./builtin/sorted.py',    'sorted'),
    'builtin.BaseException'  : ('./builtin/exception.py', 'BaseException'),
    'builtin.set'            : ('./builtin/set.py',       'set'),
    'builtin.frozenset'      : ('./builtin/set.py',       'frozenset'),

    # gateways into remote contexts
    'execnet.SocketGateway'  : ('./execnet/register.py', 'SocketGateway'),
    'execnet.PopenGateway'   : ('./execnet/register.py', 'PopenGateway'),
    'execnet.SshGateway'     : ('./execnet/register.py', 'SshGateway'),

    # execnet scripts
    'execnet.RSync'          : ('./execnet/rsync.py', 'RSync'),

    # input-output helping 
    'io.dupfile'             : ('./io/dupfile.py', 'dupfile'), 
    'io.FDCapture'           : ('./io/capture.py', 'FDCapture'), 
    'io.OutErrCapture'       : ('./io/capture.py', 'OutErrCapture'), 
    'io.callcapture'         : ('./io/capture.py', 'callcapture'), 

    # error module, defining all errno's as Classes
    'error'                  : ('./misc/error.py', 'error'),

    # small and mean xml/html generation
    'xml.html'               : ('./xmlobj/html.py', 'html'),
    'xml.Tag'                : ('./xmlobj/xml.py', 'Tag'),
    'xml.raw'                : ('./xmlobj/xml.py', 'raw'),
    'xml.Namespace'          : ('./xmlobj/xml.py', 'Namespace'),
    'xml.escape'             : ('./xmlobj/misc.py', 'escape'),

    # logging API ('producers' and 'consumers' connected via keywords)
    'log.Producer'           : ('./log/producer.py', 'Producer'),
    'log.default'            : ('./log/producer.py', 'default'),
    'log._getstate'          : ('./log/producer.py', '_getstate'),
    'log._setstate'          : ('./log/producer.py', '_setstate'),
    'log.setconsumer'        : ('./log/consumer.py', 'setconsumer'),
    'log.Path'               : ('./log/consumer.py', 'Path'),
    'log.STDOUT'             : ('./log/consumer.py', 'STDOUT'),
    'log.STDERR'             : ('./log/consumer.py', 'STDERR'),
    'log.Syslog'             : ('./log/consumer.py', 'Syslog'),
    'log.get'                : ('./log/logger.py', 'get'), 

    # compatibility modules (taken from 2.4.4) 
    'compat.doctest'         : ('./compat/doctest.py', '*'),
    'compat.optparse'        : ('./compat/optparse.py', '*'),
    'compat.textwrap'        : ('./compat/textwrap.py', '*'),
    'compat.subprocess'      : ('./compat/subprocess.py', '*'),
})
