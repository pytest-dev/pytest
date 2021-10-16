"""Add backward compatibility support for the legacy py path type."""
import subprocess
from typing import List
from typing import Optional
from typing import TYPE_CHECKING
from typing import Union

from iniconfig import SectionWrapper

import pytest
from _pytest.compat import final
from _pytest.compat import LEGACY_PATH
from _pytest.compat import legacy_path
from _pytest.deprecated import check_ispytest

if TYPE_CHECKING:
    from typing_extensions import Final

    import pexpect


@final
class Testdir:
    """
    Similar to :class:`Pytester`, but this class works with legacy legacy_path objects instead.

    All methods just forward to an internal :class:`Pytester` instance, converting results
    to `legacy_path` objects as necessary.
    """

    __test__ = False

    CLOSE_STDIN: "Final" = pytest.Pytester.CLOSE_STDIN
    TimeoutExpired: "Final" = pytest.Pytester.TimeoutExpired

    def __init__(self, pytester: pytest.Pytester, *, _ispytest: bool = False) -> None:
        check_ispytest(_ispytest)
        self._pytester = pytester

    @property
    def tmpdir(self) -> LEGACY_PATH:
        """Temporary directory where tests are executed."""
        return legacy_path(self._pytester.path)

    @property
    def test_tmproot(self) -> LEGACY_PATH:
        return legacy_path(self._pytester._test_tmproot)

    @property
    def request(self):
        return self._pytester._request

    @property
    def plugins(self):
        return self._pytester.plugins

    @plugins.setter
    def plugins(self, plugins):
        self._pytester.plugins = plugins

    @property
    def monkeypatch(self) -> pytest.MonkeyPatch:
        return self._pytester._monkeypatch

    def make_hook_recorder(self, pluginmanager) -> pytest.HookRecorder:
        """See :meth:`Pytester.make_hook_recorder`."""
        return self._pytester.make_hook_recorder(pluginmanager)

    def chdir(self) -> None:
        """See :meth:`Pytester.chdir`."""
        return self._pytester.chdir()

    def finalize(self) -> None:
        """See :meth:`Pytester._finalize`."""
        return self._pytester._finalize()

    def makefile(self, ext, *args, **kwargs) -> LEGACY_PATH:
        """See :meth:`Pytester.makefile`."""
        if ext and not ext.startswith("."):
            # pytester.makefile is going to throw a ValueError in a way that
            # testdir.makefile did not, because
            # pathlib.Path is stricter suffixes than py.path
            # This ext arguments is likely user error, but since testdir has
            # allowed this, we will prepend "." as a workaround to avoid breaking
            # testdir usage that worked before
            ext = "." + ext
        return legacy_path(self._pytester.makefile(ext, *args, **kwargs))

    def makeconftest(self, source) -> LEGACY_PATH:
        """See :meth:`Pytester.makeconftest`."""
        return legacy_path(self._pytester.makeconftest(source))

    def makeini(self, source) -> LEGACY_PATH:
        """See :meth:`Pytester.makeini`."""
        return legacy_path(self._pytester.makeini(source))

    def getinicfg(self, source: str) -> SectionWrapper:
        """See :meth:`Pytester.getinicfg`."""
        return self._pytester.getinicfg(source)

    def makepyprojecttoml(self, source) -> LEGACY_PATH:
        """See :meth:`Pytester.makepyprojecttoml`."""
        return legacy_path(self._pytester.makepyprojecttoml(source))

    def makepyfile(self, *args, **kwargs) -> LEGACY_PATH:
        """See :meth:`Pytester.makepyfile`."""
        return legacy_path(self._pytester.makepyfile(*args, **kwargs))

    def maketxtfile(self, *args, **kwargs) -> LEGACY_PATH:
        """See :meth:`Pytester.maketxtfile`."""
        return legacy_path(self._pytester.maketxtfile(*args, **kwargs))

    def syspathinsert(self, path=None) -> None:
        """See :meth:`Pytester.syspathinsert`."""
        return self._pytester.syspathinsert(path)

    def mkdir(self, name) -> LEGACY_PATH:
        """See :meth:`Pytester.mkdir`."""
        return legacy_path(self._pytester.mkdir(name))

    def mkpydir(self, name) -> LEGACY_PATH:
        """See :meth:`Pytester.mkpydir`."""
        return legacy_path(self._pytester.mkpydir(name))

    def copy_example(self, name=None) -> LEGACY_PATH:
        """See :meth:`Pytester.copy_example`."""
        return legacy_path(self._pytester.copy_example(name))

    def getnode(
        self, config: pytest.Config, arg
    ) -> Optional[Union[pytest.Item, pytest.Collector]]:
        """See :meth:`Pytester.getnode`."""
        return self._pytester.getnode(config, arg)

    def getpathnode(self, path):
        """See :meth:`Pytester.getpathnode`."""
        return self._pytester.getpathnode(path)

    def genitems(
        self, colitems: List[Union[pytest.Item, pytest.Collector]]
    ) -> List[pytest.Item]:
        """See :meth:`Pytester.genitems`."""
        return self._pytester.genitems(colitems)

    def runitem(self, source):
        """See :meth:`Pytester.runitem`."""
        return self._pytester.runitem(source)

    def inline_runsource(self, source, *cmdlineargs):
        """See :meth:`Pytester.inline_runsource`."""
        return self._pytester.inline_runsource(source, *cmdlineargs)

    def inline_genitems(self, *args):
        """See :meth:`Pytester.inline_genitems`."""
        return self._pytester.inline_genitems(*args)

    def inline_run(self, *args, plugins=(), no_reraise_ctrlc: bool = False):
        """See :meth:`Pytester.inline_run`."""
        return self._pytester.inline_run(
            *args, plugins=plugins, no_reraise_ctrlc=no_reraise_ctrlc
        )

    def runpytest_inprocess(self, *args, **kwargs) -> pytest.RunResult:
        """See :meth:`Pytester.runpytest_inprocess`."""
        return self._pytester.runpytest_inprocess(*args, **kwargs)

    def runpytest(self, *args, **kwargs) -> pytest.RunResult:
        """See :meth:`Pytester.runpytest`."""
        return self._pytester.runpytest(*args, **kwargs)

    def parseconfig(self, *args) -> pytest.Config:
        """See :meth:`Pytester.parseconfig`."""
        return self._pytester.parseconfig(*args)

    def parseconfigure(self, *args) -> pytest.Config:
        """See :meth:`Pytester.parseconfigure`."""
        return self._pytester.parseconfigure(*args)

    def getitem(self, source, funcname="test_func"):
        """See :meth:`Pytester.getitem`."""
        return self._pytester.getitem(source, funcname)

    def getitems(self, source):
        """See :meth:`Pytester.getitems`."""
        return self._pytester.getitems(source)

    def getmodulecol(self, source, configargs=(), withinit=False):
        """See :meth:`Pytester.getmodulecol`."""
        return self._pytester.getmodulecol(
            source, configargs=configargs, withinit=withinit
        )

    def collect_by_name(
        self, modcol: pytest.Collector, name: str
    ) -> Optional[Union[pytest.Item, pytest.Collector]]:
        """See :meth:`Pytester.collect_by_name`."""
        return self._pytester.collect_by_name(modcol, name)

    def popen(
        self,
        cmdargs,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=CLOSE_STDIN,
        **kw,
    ):
        """See :meth:`Pytester.popen`."""
        return self._pytester.popen(cmdargs, stdout, stderr, stdin, **kw)

    def run(self, *cmdargs, timeout=None, stdin=CLOSE_STDIN) -> pytest.RunResult:
        """See :meth:`Pytester.run`."""
        return self._pytester.run(*cmdargs, timeout=timeout, stdin=stdin)

    def runpython(self, script) -> pytest.RunResult:
        """See :meth:`Pytester.runpython`."""
        return self._pytester.runpython(script)

    def runpython_c(self, command):
        """See :meth:`Pytester.runpython_c`."""
        return self._pytester.runpython_c(command)

    def runpytest_subprocess(self, *args, timeout=None) -> pytest.RunResult:
        """See :meth:`Pytester.runpytest_subprocess`."""
        return self._pytester.runpytest_subprocess(*args, timeout=timeout)

    def spawn_pytest(
        self, string: str, expect_timeout: float = 10.0
    ) -> "pexpect.spawn":
        """See :meth:`Pytester.spawn_pytest`."""
        return self._pytester.spawn_pytest(string, expect_timeout=expect_timeout)

    def spawn(self, cmd: str, expect_timeout: float = 10.0) -> "pexpect.spawn":
        """See :meth:`Pytester.spawn`."""
        return self._pytester.spawn(cmd, expect_timeout=expect_timeout)

    def __repr__(self) -> str:
        return f"<Testdir {self.tmpdir!r}>"

    def __str__(self) -> str:
        return str(self.tmpdir)


pytest.Testdir = Testdir  # type: ignore[attr-defined]


@pytest.fixture
def testdir(pytester: pytest.Pytester) -> Testdir:
    """
    Identical to :fixture:`pytester`, and provides an instance whose methods return
    legacy ``LEGACY_PATH`` objects instead when applicable.

    New code should avoid using :fixture:`testdir` in favor of :fixture:`pytester`.
    """
    return Testdir(pytester, _ispytest=True)
