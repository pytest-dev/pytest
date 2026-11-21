# mypy: disallow-untyped-defs
"""Audit which modules :class:`_pytest.pytester.Pytester` must not destroy.

``Pytester`` snapshots ``sys.modules`` on setup and restores it on teardown,
which drops every module the test under test imported.  For most modules that
is harmless, but a module which installed *process global* state while being
imported cannot be dropped that way: the state stays behind, bound to a module
object nothing can reach anymore, and the next import creates a *second*
instance of the same module which installs the same state again.

``multiprocessing`` (see :issue:`14841`) is the motivating example - the
orphaned copy of ``multiprocessing.resource_tracker`` keeps a tracker server
process around whose bookkeeping no longer matches the live one, which then
fails loudly at interpreter shutdown.

This script probes modules one per subprocess, replaying what ``Pytester``
does, and reports the ones that ``_pytest.pytester.PRESERVED_MODULE_PACKAGES``
should cover.  It is a maintenance tool - run it by hand when adding support
for a new Python version, or when the next "module survived its own teardown"
bug shows up::

    python scripts/check-preserved-modules.py
    python scripts/check-preserved-modules.py --python python3.14 --check
    python scripts/check-preserved-modules.py --module asyncio --module random -v

Two things it cannot see: state installed by C extension modules that never
go through the Python level hooks, and state installed *after* import, on
first use - the tracker server process of the motivating example is started
lazily, and is only found here because the module registers a fork handler
while being imported.  Results are also specific to the probed interpreter and
platform, so the preserve list is the union over the interpreters pytest
supports rather than the output of a single run.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from dataclasses import field
import json
import os
from pathlib import Path
import pkgutil
import subprocess
import sys
from typing import Any


# Modules whose import is a bad idea in an unattended script: they want a
# display, block on input, open a browser, or print to stdout.
SKIP_MODULES = frozenset(
    {
        "__main__",
        "antigravity",
        "idlelib",
        "lib2to3",
        "pydoc_data",
        "site",
        "sitecustomize",
        "test",
        "this",
        "tkinter",
        "turtle",
        "turtledemo",
        "usercustomize",
    }
)

# Non-stdlib modules pytest puts in the same situation.
DEFAULT_EXTRA_MODULES = ("execnet",)


# --------------------------------------------------------------------------- #
# probe - runs in a subprocess, one module per process
# --------------------------------------------------------------------------- #


def probe(name: str) -> dict[str, Any]:
    """Import ``name``, then undo the import the way ``Pytester`` does.

    Returns what the import left behind.  This has to run in a fresh
    subprocess, because an import cannot be undone for real - which is the
    very problem being measured.
    """
    import atexit
    import importlib
    import threading
    import types

    hooks: list[tuple[str, str]] = []

    def caller() -> str:
        # 0 is this frame, 1 is the wrapper, 2 is whoever registered.
        return str(sys._getframe(2).f_globals.get("__name__", "<unknown>"))

    def recorded(kind: str, original: Any) -> Any:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            hooks.append((kind, caller()))
            return original(*args, **kwargs)

        return wrapper

    atexit.register = recorded("atexit.register", atexit.register)
    os.register_at_fork = recorded("os.register_at_fork", os.register_at_fork)
    threading._register_atexit = recorded(  # type: ignore[attr-defined]
        "threading._register_atexit",
        threading._register_atexit,  # type: ignore[attr-defined]
    )

    # A submodule is realistically imported while its package is already
    # loaded - that is what leaves a dangling reference on the package - so
    # the package belongs in the snapshot, not in the measured import.
    package = name.rpartition(".")[0]
    if package:
        importlib.import_module(package)
    hooks.clear()

    # Attributes present before the import; anything appearing on a surviving
    # module later was bound by the import and may end up dangling.
    before_attrs = {
        (modname, key)
        for modname, module in list(sys.modules.items())
        for key in list(vars(module))
    }
    before_threads = {thread.ident for thread in threading.enumerate()}
    snapshot = dict(sys.modules)

    importlib.import_module(name)

    threads = sorted(
        thread.name
        for thread in threading.enumerate()
        if thread.ident not in before_threads
    )
    imported = dict(sys.modules)

    # This is SysModulesSnapshot.restore().
    sys.modules.clear()
    sys.modules.update(snapshot)

    destroyed = set(imported) - set(sys.modules)
    dangling: set[tuple[str, str]] = set()
    for modname, module in list(sys.modules.items()):
        for key, value in list(vars(module).items()):
            if (modname, key) in before_attrs:
                continue
            owner: object
            if isinstance(value, types.ModuleType):
                owner = value.__name__
            else:
                owner = getattr(value, "__module__", None)
            if isinstance(owner, str) and owner in destroyed:
                dangling.add((f"{modname}.{key}", owner))

    return {
        "module": name,
        "hooks": sorted(set(hooks)),
        "threads": threads,
        "dangling": sorted(dangling),
        "destroyed": sorted(destroyed),
    }


# --------------------------------------------------------------------------- #
# findings
# --------------------------------------------------------------------------- #


@dataclass
class Findings:
    #: Module which installed process global state -> why it may not be
    #: destroyed.  This is what the preserve list is for.
    stateful: dict[str, set[str]] = field(default_factory=dict)
    #: Module which installed process global state -> the imports that
    #: reached it, which is how a test ends up with the module loaded.
    reached_by: dict[str, set[str]] = field(default_factory=dict)
    #: Surviving package -> the submodules it still refers to after the
    #: restore destroyed them.  Widespread and mostly harmless on its own,
    #: but it is what turns one stateful submodule into a broken package.
    torn: dict[str, set[str]] = field(default_factory=dict)

    def add(self, result: dict[str, Any]) -> None:
        imported = result["module"]
        for kind, registrant in result["hooks"]:
            # The module that registered the hook owns it, and it is often a
            # helper of the module that was actually imported.
            self.stateful.setdefault(registrant, set()).add(f"{kind}() on import")
            if registrant != imported:
                self.reached_by.setdefault(registrant, set()).add(imported)
        for thread in result["threads"]:
            self.stateful.setdefault(imported, set()).add(f"started thread {thread!r}")
        for holder, owner in result["dangling"]:
            package = holder.rpartition(".")[0]
            self.torn.setdefault(package, set()).add(owner)


def collect(results: Iterable[dict[str, Any]]) -> Findings:
    findings = Findings()
    for result in results:
        findings.add(result)
    return findings


# --------------------------------------------------------------------------- #
# candidate modules
# --------------------------------------------------------------------------- #


def run_python(python: str, code: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [python, "-c", code, *args],
        capture_output=True,
        check=False,
        text=True,
        timeout=120,
    )


def baseline_modules(python: str) -> set[str]:
    """Modules that importing pytest itself already loads.

    A module pytest imports is part of every ``Pytester`` snapshot, so it is
    never destroyed and cannot be a hazard, whatever it does on import.
    """
    completed = run_python(
        python,
        "import json, sys; import pytest, _pytest.pytester;"
        "print(json.dumps(sorted(sys.modules)))",
    )
    if completed.returncode != 0:
        print(f"warning: {python} cannot import pytest, probing everything")
        completed = run_python(
            python, "import json, sys; print(json.dumps(sorted(sys.modules)))"
        )
        completed.check_returncode()
    return set(json.loads(completed.stdout))


def candidate_modules(python: str, extra: Sequence[str]) -> list[str]:
    """Top level stdlib modules plus their immediate submodules, plus extras.

    Submodules matter as much as packages do: a package is commonly imported
    long before one of its submodules is, and that window is where the
    snapshot restore can tear a package in half.
    """
    names: set[str] = set()
    for name in [*stdlib_module_names(python), *extra]:
        if name.startswith("_") or name in SKIP_MODULES:
            continue
        names.add(name)
        names.update(submodules(python, name))
    return sorted(names)


def python_id(python: str) -> str:
    completed = run_python(
        python,
        "import platform, sys;"
        "print(sys.executable, platform.python_version(), 'on', sys.platform)",
    )
    return completed.stdout.strip() or python


def stdlib_module_names(python: str) -> list[str]:
    completed = run_python(
        python, "import json, sys; print(json.dumps(sorted(sys.stdlib_module_names)))"
    )
    completed.check_returncode()
    return json.loads(completed.stdout)  # type: ignore[no-any-return]


def submodules(python: str, name: str) -> Iterator[str]:
    """All submodules of ``name``, found without importing any of them.

    ``pkgutil.walk_packages()`` would import each package to find its
    children; descending the search locations by hand does not, which keeps
    the enumeration free of the side effects being measured.
    """
    completed = run_python(
        python,
        "import importlib.util, json, sys;"
        "spec = importlib.util.find_spec(sys.argv[1]);"
        "print(json.dumps(list(spec.submodule_search_locations or ()) if spec else []))",
        name,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        return
    yield from walk_locations(name, json.loads(completed.stdout))


def walk_locations(name: str, locations: Sequence[str]) -> Iterator[str]:
    for _, subname, is_package in pkgutil.iter_modules(list(locations)):
        if subname.startswith("_"):
            continue
        yield f"{name}.{subname}"
        if is_package:
            yield from walk_locations(
                f"{name}.{subname}",
                [os.path.join(location, subname) for location in locations],
            )


# --------------------------------------------------------------------------- #
# report
# --------------------------------------------------------------------------- #


def preserve_rule() -> tuple[frozenset[str], Callable[[str], bool]]:
    """The list under audit and its matching rule, from the source of truth."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    from _pytest.pytester import module_is_preserved
    from _pytest.pytester import PRESERVED_MODULE_PACKAGES

    return PRESERVED_MODULE_PACKAGES, module_is_preserved


def heading(title: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}")


def report(
    findings: Findings,
    packages: Iterable[str],
    is_preserved: Callable[[str], bool],
    verbose: bool,
) -> list[str]:
    """Print the report; return the modules the preserve list does not cover."""
    missing = [name for name in sorted(findings.stateful) if not is_preserved(name)]

    heading(f"Modules installing process global state ({len(findings.stateful)})")
    for name in sorted(findings.stateful):
        package = name.partition(".")[0]
        status = f"preserved via {package!r}" if is_preserved(name) else "NOT PRESERVED"
        print(f"\n{name}  [{status}]")
        for reason in sorted(findings.stateful[name]):
            print(f"    {reason}")
        via = sorted(findings.reached_by.get(name, ()))
        if via:
            shown = ", ".join(via[:5])
            more = f", ... (+{len(via) - 5})" if len(via) > 5 else ""
            print(f"    imported by: {shown}{more}")

    heading(f"Packages torn in half by the restore ({len(findings.torn)})")
    print(
        "The package survives in sys.modules while the submodule it refers to\n"
        "does not, so the next import of that submodule builds a second copy.\n"
        "Harmless unless the submodule is listed above - which is why preserve\n"
        "entries are whole top level packages."
    )
    for package in sorted(findings.torn):
        if verbose:
            print(f"    {package}: {', '.join(sorted(findings.torn[package]))}")
        elif findings.stateful.keys() & findings.torn[package]:
            print(f"    {package} (holds stateful submodules)")

    heading("Summary")
    print(f"preserve list: {', '.join(sorted(packages))}")
    if missing:
        print(f"not covered by it: {', '.join(missing)}")
    else:
        print("not covered by it: nothing")
    return missing


# --------------------------------------------------------------------------- #
# driver
# --------------------------------------------------------------------------- #


def run_probe(python: str, name: str) -> dict[str, Any] | None:
    """Run ``probe(name)`` in a subprocess; ``None`` if the import failed."""
    completed = subprocess.run(
        [python, str(Path(__file__).resolve()), "--probe", name],
        capture_output=True,
        check=False,
        text=True,
        timeout=120,
    )
    if completed.returncode != 0:
        return None
    return json.loads(completed.stdout)  # type: ignore[no-any-return]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--probe", metavar="MODULE", help=argparse.SUPPRESS)
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="interpreter to probe (default: the one running this script)",
    )
    parser.add_argument(
        "--extra",
        action="append",
        default=[],
        metavar="MODULE",
        help=f"also probe a non-stdlib module (default: {', '.join(DEFAULT_EXTRA_MODULES)})",
    )
    parser.add_argument(
        "--module",
        action="append",
        default=[],
        metavar="MODULE",
        help="probe only these modules instead of the whole stdlib",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=min(32, (os.cpu_count() or 1) * 4),
        help="number of probe subprocesses to run in parallel",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="list every torn package"
    )
    parser.add_argument(
        "--json", action="store_true", help="dump raw probe results instead of a report"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if the preserve list misses a module",
    )
    args = parser.parse_args(argv)

    if args.probe:
        json.dump(probe(args.probe), sys.stdout)
        return 0

    python = args.python
    extra = args.extra or list(DEFAULT_EXTRA_MODULES)
    if args.module:
        candidates = sorted(set(args.module))
    else:
        baseline = baseline_modules(python)
        candidates = [
            name for name in candidate_modules(python, extra) if name not in baseline
        ]

    print(f"probing {len(candidates)} modules with {args.jobs} jobs ...", flush=True)
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        probed = executor.map(lambda name: run_probe(python, name), candidates)
        results = [result for result in probed if result is not None]
    print(f"{len(results)} of {len(candidates)} modules imported cleanly")

    if args.json:
        json.dump(results, sys.stdout, indent=1)
        return 0

    packages, is_preserved = preserve_rule()
    missing = report(collect(results), packages, is_preserved, args.verbose)
    print(f"probed: {python_id(python)}")
    return 1 if args.check and missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
