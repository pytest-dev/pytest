""" support for providing temporary directories to test functions.  """
from __future__ import absolute_import, division, print_function

import re
from six.moves import reduce

import pytest
import py
from _pytest.monkeypatch import MonkeyPatch
from .compat import Path
import attr
import shutil
import tempfile


def make_numbered_dir(root, prefix):
    l_prefix = prefix.lower()

    def parse_num(p, cut=len(l_prefix)):
        maybe_num = p.name[cut:]
        try:
            return int(maybe_num)
        except ValueError:
            return -1

    for i in range(10):
        # try up to 10 times to create the folder
        max_existing = reduce(
            max,
            (
                parse_num(x)
                for x in root.iterdir()
                if x.name.lower().startswith(l_prefix)
            ),
            -1,
        )
        new_number = max_existing + 1
        new_path = root.joinpath("{}{}".format(prefix, new_number))
        try:
            new_path.mkdir()
        except Exception:
            pass
        else:
            return new_path


def make_numbered_dir_with_cleanup(root, prefix, keep, consider_lock_dead_after):
    p = make_numbered_dir(root, prefix)
    # todo cleanup
    return p


@attr.s
class TempPathFactory(object):
    """docstring for ClassName"""

    given_basetemp = attr.ib()
    trace = attr.ib()
    _basetemp = attr.ib(default=None)

    @classmethod
    def from_config(cls, config):
        return cls(
            given_basetemp=config.option.basetemp, trace=config.trace.get("tmpdir")
        )

    def mktemp(self, basename, numbered=True):
        if not numbered:
            p = self.getbasetemp().joinpath(basename)
            p.mkdir()
        else:
            p = make_numbered_dir(root=self.getbasetemp(), prefix=basename)
            self.trace("mktemp", p)
        return p

    def getbasetemp(self):
        """ return base temporary directory. """
        if self._basetemp is None:
            if self.given_basetemp:
                basetemp = Path(self.given_basetemp)
                if basetemp.exists():
                    shutil.rmtree(str(basetemp))
                basetemp.mkdir()
            else:
                temproot = Path(tempfile.gettempdir())
                user = get_user()
                if user:
                    # use a sub-directory in the temproot to speed-up
                    # make_numbered_dir() call
                    rootdir = temproot.joinpath("pytest-of-{}".format(user))
                else:
                    rootdir = temproot
                rootdir.mkdir(exist_ok=True)
                basetemp = make_numbered_dir_with_cleanup(
                    prefix="pytest-",
                    root=rootdir,
                    keep=None,
                    consider_lock_dead_after=None,
                )
            self._basetemp = t = basetemp
            self.trace("new basetemp", t)
            return t
        else:
            return self._basetemp


@attr.s
class TempdirFactory(object):
    """Factory for temporary directories under the common base temp directory.

    The base directory can be configured using the ``--basetemp`` option.
    """

    tmppath_factory = attr.ib()

    def ensuretemp(self, string, dir=1):
        """ (deprecated) return temporary directory path with
            the given string as the trailing part.  It is usually
            better to use the 'tmpdir' function argument which
            provides an empty unique-per-test-invocation directory
            and is guaranteed to be empty.
        """
        # py.log._apiwarn(">1.1", "use tmpdir function argument")
        return self.getbasetemp().ensure(string, dir=dir)

    def mktemp(self, basename, numbered=True):
        """Create a subdirectory of the base temporary directory and return it.
        If ``numbered``, ensure the directory is unique by adding a number
        prefix greater than any existing one.
        """
        return py.path.local(self.tmppath_factory.mktemp(basename, numbered).resolve())

    def getbasetemp(self):
        return py.path.local(self.tmppath_factory.getbasetemp().resolve())

    def finish(self):
        self.tmppath_factory.trace("finish")


def get_user():
    """Return the current user name, or None if getuser() does not work
    in the current environment (see #1010).
    """
    import getpass

    try:
        return getpass.getuser()
    except (ImportError, KeyError):
        return None


def pytest_configure(config):
    """Create a TempdirFactory and attach it to the config object.

    This is to comply with existing plugins which expect the handler to be
    available at pytest_configure time, but ideally should be moved entirely
    to the tmpdir_factory session fixture.
    """
    mp = MonkeyPatch()
    tmppath_handler = TempPathFactory.from_config(config)
    t = TempdirFactory(tmppath_handler)
    config._cleanup.extend([mp.undo, t.finish])
    mp.setattr(config, "_tmpdirhandler", t, raising=False)
    mp.setattr(pytest, "ensuretemp", t.ensuretemp, raising=False)


@pytest.fixture(scope="session")
def tmpdir_factory(request):
    """Return a TempdirFactory instance for the test session.
    """
    return request.config._tmpdirhandler


@pytest.fixture
def tmpdir(request, tmpdir_factory):
    """Return a temporary directory path object
    which is unique to each test function invocation,
    created as a sub directory of the base temporary
    directory.  The returned object is a `py.path.local`_
    path object.

    .. _`py.path.local`: https://py.readthedocs.io/en/latest/path.html
    """
    name = request.node.name
    name = re.sub(r"[\W]", "_", name)
    MAXVAL = 30
    if len(name) > MAXVAL:
        name = name[:MAXVAL]
    x = tmpdir_factory.mktemp(name, numbered=True)
    return x
