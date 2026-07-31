"""In-memory collection for scenarios (EXPERIMENTAL)."""

from __future__ import annotations

from collections.abc import Callable
from collections.abc import Iterator
import contextlib
import types

from _pytest.config import Config
from _pytest.config import ExitCode
from _pytest.main import Session
from _pytest.nodes import Collector
from _pytest.nodes import Item
from _pytest.python import Module
from _pytest.reports import CollectReport
from _pytest.scenario.results import ensure_recorder


#: A test source: a module-like object collected as a virtual module, or a
#: loose class/callable wrapped into a synthesized one.
Source = types.ModuleType | type | Callable[..., object]


class ScenarioModule(Module):
    """A Module collector backed by an in-memory python object.

    The synthetic ``path`` is rootdir-relative (giving well-formed nodeids)
    but never touched on disk; the standard import chokepoint is bypassed
    by serving the preset object from ``_getobj``.
    """

    _scenario_obj: types.ModuleType

    @classmethod
    def from_parent(  # type: ignore[override]
        cls,
        parent: Session,
        *,
        obj: types.ModuleType,
        name: str | None = None,
    ) -> ScenarioModule:
        """The public constructor."""
        if name is None:
            name = obj.__name__
        path = parent.config.rootpath / f"{name}.py"
        node: ScenarioModule = super().from_parent(parent, path=path)
        node._scenario_obj = obj
        return node

    def _getobj(self) -> types.ModuleType:
        return self._scenario_obj


class ScenarioCollection:
    """Plugin serving a preset list of collectors as the session's
    collection tree, instead of walking filesystem paths."""

    name = "scenario-collection"

    def __init__(self, session: Session) -> None:
        self.session = session
        self.collectors: list[Collector] = []

    def pytest_make_collect_report(self, collector: Collector) -> CollectReport | None:
        if collector is self.session:
            return CollectReport(
                collector.nodeid, "passed", None, list(self.collectors)
            )
        return None


def scenario_collection(session: Session) -> ScenarioCollection:
    """Get the preset-collection plugin for the session, installing it if needed."""
    plugin: ScenarioCollection | None = session.config.pluginmanager.get_plugin(
        ScenarioCollection.name
    )
    if plugin is None:
        plugin = ScenarioCollection(session)
        session.config.pluginmanager.register(plugin, ScenarioCollection.name)
    assert plugin.session is session
    return plugin


@contextlib.contextmanager
def running_session(config: Config) -> Iterator[Session]:
    """A started :class:`Session` for a configured scenario config.

    ``pytest_sessionstart`` runs on enter (installing ``SetupState`` and the
    ``FixtureManager``); ``pytest_sessionfinish`` runs on exit.
    """
    session = Session.from_config(config)
    ensure_recorder(config)
    scenario_collection(session)
    config.hook.pytest_sessionstart(session=session)
    exitstatus: int | ExitCode = ExitCode.OK
    try:
        yield session
    except BaseException:
        exitstatus = ExitCode.INTERNAL_ERROR
        raise
    finally:
        config.hook.pytest_sessionfinish(session=session, exitstatus=exitstatus)


def fake_module(
    name: str, *members: object, **named_members: object
) -> types.ModuleType:
    """Create an in-memory module with an explicit name, collecting the
    given members together.

    Positional members are stored under their ``__name__``; keyword
    members under the given keyword (e.g. ``pytestmark=...``).
    """
    module = types.ModuleType(name)
    for member in members:
        member_name = getattr(member, "__name__", None)
        if member_name is None:
            raise ValueError(
                f"member {member!r} has no __name__; pass it as a keyword instead"
            )
        setattr(module, member_name, member)
    for member_name, member in named_members.items():
        setattr(module, member_name, member)
    return module


def collect_objects(
    session: Session,
    *sources: Source,
    name: str = "scenario_module",
) -> list[Item]:
    """Collect test items from in-memory objects through the standard
    collection protocol.

    Module-like sources each become a :class:`ScenarioModule`; loose
    classes and callables are wrapped into one synthesized module named
    ``name``. The regular ``pytest_collection`` hook then runs, so
    ``-k``/``-m`` deselection, ``pytest_collection_modifyitems`` and
    ``pytest_collection_finish`` all apply.
    """
    config = session.config
    collection = scenario_collection(session)
    loose: list[object] = []
    for source in sources:
        if isinstance(source, types.ModuleType):
            collection.collectors.append(
                ScenarioModule.from_parent(session, obj=source)
            )
        else:
            loose.append(source)
    if loose:
        module = fake_module(name, *loose)
        if not config.getini("collect_imported_tests"):
            # python.py drops objects whose __module__ differs from the
            # containing module; synthesized namespaces always differ.
            raise ValueError(
                "collect_imported_tests=False would silently drop loose "
                "scenario sources; pass a real module object instead"
            )
        collection.collectors.append(
            ScenarioModule.from_parent(session, obj=module, name=name)
        )

    config.hook.pytest_collection(session=session)
    return session.items
