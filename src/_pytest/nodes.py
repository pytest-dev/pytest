import os
import warnings
from functools import lru_cache
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

import py

import _pytest._code
from _pytest._code.code import ExceptionChainRepr
from _pytest._code.code import ExceptionInfo
from _pytest._code.code import ReprExceptionInfo
from _pytest._code.source import getfslineno
from _pytest.compat import cached_property
from _pytest.compat import TYPE_CHECKING
from _pytest.config import Config
from _pytest.config import ConftestImportFailure
from _pytest.config import PytestPluginManager
from _pytest.deprecated import NODE_USE_FROM_PARENT
from _pytest.fixtures import FixtureDef
from _pytest.fixtures import FixtureLookupError
from _pytest.fixtures import FixtureLookupErrorRepr
from _pytest.mark.structures import Mark
from _pytest.mark.structures import MarkDecorator
from _pytest.mark.structures import NodeKeywords
from _pytest.outcomes import fail
from _pytest.pathlib import Path
from _pytest.store import Store

if TYPE_CHECKING:
    # Imported here due to circular import.
    from _pytest.main import Session  # noqa: F401

SEP = "/"

tracebackcutdir = py.path.local(_pytest.__file__).dirpath()


@lru_cache(maxsize=None)
def _splitnode(nodeid):
    """Split a nodeid into constituent 'parts'.

    Node IDs are strings, and can be things like:
        ''
        'testing/code'
        'testing/code/test_excinfo.py'
        'testing/code/test_excinfo.py::TestFormattedExcinfo'

    Return values are lists e.g.
        []
        ['testing', 'code']
        ['testing', 'code', 'test_excinfo.py']
        ['testing', 'code', 'test_excinfo.py', 'TestFormattedExcinfo']
    """
    if nodeid == "":
        # If there is no root node at all, return an empty list so the caller's logic can remain sane
        return ()
    parts = nodeid.split(SEP)
    # Replace single last element 'test_foo.py::Bar' with multiple elements 'test_foo.py', 'Bar'
    parts[-1:] = parts[-1].split("::")
    # Convert parts into a tuple to avoid possible errors with caching of a mutable type
    return tuple(parts)


def ischildnode(baseid, nodeid):
    """Return True if the nodeid is a child node of the baseid.

    E.g. 'foo/bar::Baz' is a child of 'foo', 'foo/bar' and 'foo/bar::Baz', but not of 'foo/blorp'
    """
    base_parts = _splitnode(baseid)
    node_parts = _splitnode(nodeid)
    if len(node_parts) < len(base_parts):
        return False
    return node_parts[: len(base_parts)] == base_parts


class NodeMeta(type):
    def __call__(self, *k, **kw):
        warnings.warn(NODE_USE_FROM_PARENT.format(name=self.__name__), stacklevel=2)
        return super().__call__(*k, **kw)

    def _create(self, *k, **kw):
        return super().__call__(*k, **kw)


class Node(metaclass=NodeMeta):
    """ base class for Collector and Item the test collection tree.
    Collector subclasses have children, Items are terminal nodes."""

    def __init__(
        self,
        name: str,
        parent: Optional["Node"] = None,
        config: Optional[Config] = None,
        session: Optional["Session"] = None,
        fspath: Optional[py.path.local] = None,
        nodeid: Optional[str] = None,
    ) -> None:
        #: a unique name within the scope of the parent node
        self.name = name

        #: the parent collector node.
        self.parent = parent

        #: the pytest config object
        if config:
            self.config = config
        else:
            if not parent:
                raise TypeError("config or parent must be provided")
            self.config = parent.config

        #: the session this node is part of
        if session:
            self.session = session
        else:
            if not parent:
                raise TypeError("session or parent must be provided")
            self.session = parent.session

        #: filesystem path where this node was collected from (can be None)
        self.fspath = fspath or getattr(parent, "fspath", None)

        #: keywords/markers collected from all scopes
        self.keywords = NodeKeywords(self)

        #: the marker objects belonging to this node
        self.own_markers = []  # type: List[Mark]

        #: allow adding of extra keywords to use for matching
        self.extra_keyword_matches = set()  # type: Set[str]

        # used for storing artificial fixturedefs for direct parametrization
        self._name2pseudofixturedef = {}  # type: Dict[str, FixtureDef]

        if nodeid is not None:
            assert "::()" not in nodeid
            self._nodeid = nodeid
        else:
            if not self.parent:
                raise TypeError("nodeid or parent must be provided")
            self._nodeid = self.parent.nodeid
            if self.name != "()":
                self._nodeid += "::" + self.name

        # A place where plugins can store information on the node for their
        # own use. Currently only intended for internal plugins.
        self._store = Store()

    @classmethod
    def from_parent(cls, parent: "Node", **kw):
        """
        Public Constructor for Nodes

        This indirection got introduced in order to enable removing
        the fragile logic from the node constructors.

        Subclasses can use ``super().from_parent(...)`` when overriding the construction

        :param parent: the parent node of this test Node
        """
        if "config" in kw:
            raise TypeError("config is not a valid argument for from_parent")
        if "session" in kw:
            raise TypeError("session is not a valid argument for from_parent")
        return cls._create(parent=parent, **kw)

    @property
    def ihook(self):
        """ fspath sensitive hook proxy used to call pytest hooks"""
        return self.session.gethookproxy(self.fspath)

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, getattr(self, "name", None))

    def warn(self, warning):
        """Issue a warning for this item.

        Warnings will be displayed after the test session, unless explicitly suppressed

        :param Warning warning: the warning instance to issue. Must be a subclass of PytestWarning.

        :raise ValueError: if ``warning`` instance is not a subclass of PytestWarning.

        Example usage:

        .. code-block:: python

            node.warn(PytestWarning("some message"))

        """
        from _pytest.warning_types import PytestWarning

        if not isinstance(warning, PytestWarning):
            raise ValueError(
                "warning must be an instance of PytestWarning or subclass, got {!r}".format(
                    warning
                )
            )
        path, lineno = get_fslocation_from_item(self)
        warnings.warn_explicit(
            warning,
            category=None,
            filename=str(path),
            lineno=lineno + 1 if lineno is not None else None,
        )

    # methods for ordering nodes
    @property
    def nodeid(self):
        """ a ::-separated string denoting its collection tree address. """
        return self._nodeid

    def __hash__(self):
        return hash(self.nodeid)

    def setup(self):
        pass

    def teardown(self):
        pass

    def listchain(self):
        """ return list of all parent collectors up to self,
            starting from root of collection tree. """
        chain = []
        item = self  # type: Optional[Node]
        while item is not None:
            chain.append(item)
            item = item.parent
        chain.reverse()
        return chain

    def add_marker(
        self, marker: Union[str, MarkDecorator], append: bool = True
    ) -> None:
        """dynamically add a marker object to the node.

        :type marker: ``str`` or ``pytest.mark.*``  object
        :param marker:
            ``append=True`` whether to append the marker,
            if ``False`` insert at position ``0``.
        """
        from _pytest.mark import MARK_GEN

        if isinstance(marker, MarkDecorator):
            marker_ = marker
        elif isinstance(marker, str):
            marker_ = getattr(MARK_GEN, marker)
        else:
            raise ValueError("is not a string or pytest.mark.* Marker")
        self.keywords[marker_.name] = marker
        if append:
            self.own_markers.append(marker_.mark)
        else:
            self.own_markers.insert(0, marker_.mark)

    def iter_markers(self, name=None):
        """
        :param name: if given, filter the results by the name attribute

        iterate over all markers of the node
        """
        return (x[1] for x in self.iter_markers_with_node(name=name))

    def iter_markers_with_node(self, name=None):
        """
        :param name: if given, filter the results by the name attribute

        iterate over all markers of the node
        returns sequence of tuples (node, mark)
        """
        for node in reversed(self.listchain()):
            for mark in node.own_markers:
                if name is None or getattr(mark, "name", None) == name:
                    yield node, mark

    def get_closest_marker(self, name, default=None):
        """return the first marker matching the name, from closest (for example function) to farther level (for example
        module level).

        :param default: fallback return value of no marker was found
        :param name: name to filter by
        """
        return next(self.iter_markers(name=name), default)

    def listextrakeywords(self):
        """ Return a set of all extra keywords in self and any parents."""
        extra_keywords = set()  # type: Set[str]
        for item in self.listchain():
            extra_keywords.update(item.extra_keyword_matches)
        return extra_keywords

    def listnames(self):
        return [x.name for x in self.listchain()]

    def addfinalizer(self, fin):
        """ register a function to be called when this node is finalized.

        This method can only be called when this node is active
        in a setup chain, for example during self.setup().
        """
        self.session._setupstate.addfinalizer(fin, self)

    def getparent(self, cls):
        """ get the next parent node (including ourself)
        which is an instance of the given class"""
        current = self  # type: Optional[Node]
        while current and not isinstance(current, cls):
            current = current.parent
        return current

    def _prunetraceback(self, excinfo):
        pass

    def _repr_failure_py(
        self, excinfo: ExceptionInfo[BaseException], style=None,
    ) -> Union[str, ReprExceptionInfo, ExceptionChainRepr, FixtureLookupErrorRepr]:
        if isinstance(excinfo.value, ConftestImportFailure):
            excinfo = ExceptionInfo(excinfo.value.excinfo)
        if isinstance(excinfo.value, fail.Exception):
            if not excinfo.value.pytrace:
                return str(excinfo.value)
        if isinstance(excinfo.value, FixtureLookupError):
            return excinfo.value.formatrepr()
        if self.config.getoption("fulltrace", False):
            style = "long"
        else:
            tb = _pytest._code.Traceback([excinfo.traceback[-1]])
            self._prunetraceback(excinfo)
            if len(excinfo.traceback) == 0:
                excinfo.traceback = tb
            if style == "auto":
                style = "long"
        # XXX should excinfo.getrepr record all data and toterminal() process it?
        if style is None:
            if self.config.getoption("tbstyle", "auto") == "short":
                style = "short"
            else:
                style = "long"

        if self.config.getoption("verbose", 0) > 1:
            truncate_locals = False
        else:
            truncate_locals = True

        # excinfo.getrepr() formats paths relative to the CWD if `abspath` is False.
        # It is possible for a fixture/test to change the CWD while this code runs, which
        # would then result in the user seeing confusing paths in the failure message.
        # To fix this, if the CWD changed, always display the full absolute path.
        # It will be better to just always display paths relative to invocation_dir, but
        # this requires a lot of plumbing (#6428).
        try:
            abspath = Path(os.getcwd()) != Path(self.config.invocation_dir)
        except OSError:
            abspath = True

        return excinfo.getrepr(
            funcargs=True,
            abspath=abspath,
            showlocals=self.config.getoption("showlocals", False),
            style=style,
            tbfilter=False,  # pruned already, or in --fulltrace mode.
            truncate_locals=truncate_locals,
        )

    def repr_failure(
        self, excinfo, style=None
    ) -> Union[str, ReprExceptionInfo, ExceptionChainRepr, FixtureLookupErrorRepr]:
        return self._repr_failure_py(excinfo, style)


def get_fslocation_from_item(
    item: "Item",
) -> Tuple[Union[str, py.path.local], Optional[int]]:
    """Tries to extract the actual location from an item, depending on available attributes:

    * "fslocation": a pair (path, lineno)
    * "obj": a Python object that the item wraps.
    * "fspath": just a path

    :rtype: a tuple of (str|LocalPath, int) with filename and line number.
    """
    try:
        return item.location[:2]
    except AttributeError:
        pass
    obj = getattr(item, "obj", None)
    if obj is not None:
        return getfslineno(obj)
    return getattr(item, "fspath", "unknown location"), -1


class Collector(Node):
    """ Collector instances create children through collect()
        and thus iteratively build a tree.
    """

    class CollectError(Exception):
        """ an error during collection, contains a custom message. """

    def collect(self):
        """ returns a list of children (items and collectors)
            for this collection node.
        """
        raise NotImplementedError("abstract")

    def repr_failure(self, excinfo):
        """ represent a collection failure. """
        if excinfo.errisinstance(self.CollectError) and not self.config.getoption(
            "fulltrace", False
        ):
            exc = excinfo.value
            return str(exc.args[0])

        # Respect explicit tbstyle option, but default to "short"
        # (_repr_failure_py uses "long" with "fulltrace" option always).
        tbstyle = self.config.getoption("tbstyle", "auto")
        if tbstyle == "auto":
            tbstyle = "short"

        return self._repr_failure_py(excinfo, style=tbstyle)

    def _prunetraceback(self, excinfo):
        if hasattr(self, "fspath"):
            traceback = excinfo.traceback
            ntraceback = traceback.cut(path=self.fspath)
            if ntraceback == traceback:
                ntraceback = ntraceback.cut(excludepath=tracebackcutdir)
            excinfo.traceback = ntraceback.filter()


def _check_initialpaths_for_relpath(session, fspath):
    for initial_path in session._initialpaths:
        if fspath.common(initial_path) == initial_path:
            return fspath.relto(initial_path)


class FSHookProxy:
    def __init__(
        self, fspath: py.path.local, pm: PytestPluginManager, remove_mods
    ) -> None:
        self.fspath = fspath
        self.pm = pm
        self.remove_mods = remove_mods

    def __getattr__(self, name: str):
        x = self.pm.subset_hook_caller(name, remove_plugins=self.remove_mods)
        self.__dict__[name] = x
        return x


class FSCollector(Collector):
    def __init__(
        self, fspath: py.path.local, parent=None, config=None, session=None, nodeid=None
    ) -> None:
        name = fspath.basename
        if parent is not None:
            rel = fspath.relto(parent.fspath)
            if rel:
                name = rel
            name = name.replace(os.sep, SEP)
        self.fspath = fspath

        session = session or parent.session

        if nodeid is None:
            nodeid = self.fspath.relto(session.config.rootdir)

            if not nodeid:
                nodeid = _check_initialpaths_for_relpath(session, fspath)
            if nodeid and os.sep != SEP:
                nodeid = nodeid.replace(os.sep, SEP)

        super().__init__(name, parent, config, session, nodeid=nodeid, fspath=fspath)

        self._norecursepatterns = self.config.getini("norecursedirs")

    @classmethod
    def from_parent(cls, parent, *, fspath, **kw):
        """
        The public constructor
        """
        return super().from_parent(parent=parent, fspath=fspath, **kw)

    def _gethookproxy(self, fspath: py.path.local):
        # check if we have the common case of running
        # hooks with all conftest.py files
        pm = self.config.pluginmanager
        my_conftestmodules = pm._getconftestmodules(fspath)
        remove_mods = pm._conftest_plugins.difference(my_conftestmodules)
        if remove_mods:
            # one or more conftests are not in use at this fspath
            proxy = FSHookProxy(fspath, pm, remove_mods)
        else:
            # all plugins are active for this fspath
            proxy = self.config.hook
        return proxy

    def _recurse(self, dirpath: py.path.local) -> bool:
        if dirpath.basename == "__pycache__":
            return False
        ihook = self._gethookproxy(dirpath.dirpath())
        if ihook.pytest_ignore_collect(path=dirpath, config=self.config):
            return False
        for pat in self._norecursepatterns:
            if dirpath.check(fnmatch=pat):
                return False
        ihook = self._gethookproxy(dirpath)
        ihook.pytest_collect_directory(path=dirpath, parent=self)
        return True

    def _collectfile(self, path, handle_dupes=True):
        assert (
            path.isfile()
        ), "{!r} is not a file (isdir={!r}, exists={!r}, islink={!r})".format(
            path, path.isdir(), path.exists(), path.islink()
        )
        ihook = self.gethookproxy(path)
        if not self.isinitpath(path):
            if ihook.pytest_ignore_collect(path=path, config=self.config):
                return ()

        if handle_dupes:
            keepduplicates = self.config.getoption("keepduplicates")
            if not keepduplicates:
                duplicate_paths = self.config.pluginmanager._duplicatepaths
                if path in duplicate_paths:
                    return ()
                else:
                    duplicate_paths.add(path)

        return ihook.pytest_collect_file(path=path, parent=self)


class File(FSCollector):
    """ base class for collecting tests from a file. """


class Item(Node):
    """ a basic test invocation item. Note that for a single function
    there might be multiple test invocation items.
    """

    nextitem = None

    def __init__(self, name, parent=None, config=None, session=None, nodeid=None):
        super().__init__(name, parent, config, session, nodeid=nodeid)
        self._report_sections = []  # type: List[Tuple[str, str, str]]

        #: user properties is a list of tuples (name, value) that holds user
        #: defined properties for this test.
        self.user_properties = []  # type: List[Tuple[str, Any]]

    def runtest(self) -> None:
        raise NotImplementedError("runtest must be implemented by Item subclass")

    def add_report_section(self, when: str, key: str, content: str) -> None:
        """
        Adds a new report section, similar to what's done internally to add stdout and
        stderr captured output::

            item.add_report_section("call", "stdout", "report section contents")

        :param str when:
            One of the possible capture states, ``"setup"``, ``"call"``, ``"teardown"``.
        :param str key:
            Name of the section, can be customized at will. Pytest uses ``"stdout"`` and
            ``"stderr"`` internally.

        :param str content:
            The full contents as a string.
        """
        if content:
            self._report_sections.append((when, key, content))

    def reportinfo(self) -> Tuple[Union[py.path.local, str], Optional[int], str]:
        return self.fspath, None, ""

    @cached_property
    def location(self) -> Tuple[str, Optional[int], str]:
        location = self.reportinfo()
        if isinstance(location[0], py.path.local):
            fspath = location[0]
        else:
            fspath = py.path.local(location[0])
        relfspath = self.session._node_location_to_relpath(fspath)
        assert type(location[2]) is str
        return (relfspath, location[1], location[2])
