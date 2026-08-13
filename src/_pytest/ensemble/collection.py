"""In-memory collection for ensembles (EXPERIMENTAL)."""

from __future__ import annotations

from collections.abc import Callable
from collections.abc import Iterator
import contextlib
import types
from typing import Final

from _pytest.config import Config
from _pytest.config import ExitCode
from _pytest.ensemble.results import ensure_recorder
from _pytest.main import Session
from _pytest.nodes import Collector
from _pytest.nodes import Item
from _pytest.python import Module
from _pytest.reports import CollectReport


#: A test source: a module-like object collected as a virtual module, or a
#: loose class/callable wrapped into a synthesized one.
Source = types.ModuleType | type | Callable[..., object]

#: Default name for the synthesized module holding loose sources.
DEFAULT_MODULE_NAME: Final[str] = "test_ensemble"


class EnsembleModule(Module):
    """A Module collector backed by an in-memory python object.

    The synthetic ``path`` is rootdir-relative (giving well-formed nodeids)
    but never touched on disk; the standard import chokepoint is bypassed
    by serving the preset object from ``_getobj``.
    """

    _preset_obj: types.ModuleType

    @classmethod
    def from_parent(  # type: ignore[override]
        cls,
        parent: Session,
        *,
        obj: types.ModuleType,
        name: str | None = None,
    ) -> EnsembleModule:
        """The public constructor."""
        if name is None:
            name = obj.__name__
        path = parent.config.rootpath / f"{name}.py"
        node: EnsembleModule = super().from_parent(parent, path=path)
        node._preset_obj = obj
        return node

    def _getobj(self) -> types.ModuleType:
        return self._preset_obj


class EnsembleCollection:
    """Plugin serving a preset list of collectors as the session's
    collection tree, instead of walking filesystem paths."""

    name = "ensemble-collection"

    def __init__(self, session: Session) -> None:
        self.session = session
        self.collectors: list[Collector] = []

    def pytest_make_collect_report(self, collector: Collector) -> CollectReport | None:
        if collector is self.session:
            return CollectReport(
                collector.nodeid, "passed", None, list(self.collectors)
            )
        return None


def ensemble_collection(session: Session) -> EnsembleCollection:
    """Get the preset-collection plugin for the session, installing it if needed."""
    plugin: EnsembleCollection | None = session.config.pluginmanager.get_plugin(
        EnsembleCollection.name
    )
    if plugin is None:
        plugin = EnsembleCollection(session)
        session.config.pluginmanager.register(plugin, EnsembleCollection.name)
    assert plugin.session is session
    return plugin


@contextlib.contextmanager
def running_session(config: Config) -> Iterator[Session]:
    """A started :class:`Session` for a configured ensemble config.

    ``pytest_sessionstart`` runs on enter (installing ``SetupState`` and the
    ``FixtureManager``); ``pytest_sessionfinish`` runs on exit.
    """
    session = Session.from_config(config)
    ensure_recorder(config)
    ensemble_collection(session)
    config.hook.pytest_sessionstart(session=session)
    exitstatus: int | ExitCode = ExitCode.OK
    try:
        yield session
    except BaseException:
        exitstatus = ExitCode.INTERNAL_ERROR
        raise
    finally:
        config.hook.pytest_sessionfinish(session=session, exitstatus=exitstatus)


def build_module(
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


def collect_sources(
    session: Session,
    *sources: Source,
    name: str = DEFAULT_MODULE_NAME,
) -> list[Item]:
    """Collect test items from in-memory objects through the standard
    collection protocol.

    Module-like sources each become a :class:`EnsembleModule`; loose
    classes and callables are wrapped into one synthesized module named
    ``name``. The regular ``pytest_collection`` hook then runs, so
    ``-k``/``-m`` deselection, ``pytest_collection_modifyitems`` and
    ``pytest_collection_finish`` all apply.
    """
    config = session.config
    collection = ensemble_collection(session)
    loose: list[object] = []
    for source in sources:
        if isinstance(source, types.ModuleType):
            collection.collectors.append(
                EnsembleModule.from_parent(session, obj=source)
            )
        else:
            loose.append(source)
    if loose:
        module = build_module(name, *loose)
        if not config.getini("collect_imported_tests"):
            # python.py drops objects whose __module__ differs from the
            # containing module; synthesized namespaces always differ.
            raise ValueError(
                "collect_imported_tests=False would silently drop loose "
                "ensemble sources; pass a real module object instead"
            )
        collection.collectors.append(
            EnsembleModule.from_parent(session, obj=module, name=name)
        )

    config.hook.pytest_collection(session=session)
    return session.items
