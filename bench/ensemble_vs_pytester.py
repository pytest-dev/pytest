"""Compare the cost of the pytester harness against ``_pytest.ensemble``.

pytest's own test suite is dominated by pytester-based tests: they write a
module to disk and run a full session against it. ``_pytest.ensemble`` runs
tests from in-memory objects in a reduced, hermetic configuration. This
script measures what that difference costs per run.

The arms are, from heaviest to lightest:

``subprocess``
    ``makepyfile`` + ``runpytest_subprocess`` - a whole new interpreter.
``inprocess``
    ``makepyfile`` + ``runpytest_inprocess`` - full config, capture and
    terminal, with the rendered output captured for matching.
``inline``
    ``makepyfile`` + ``inline_run`` - same session, but no terminal
    reporting or output parsing.
``ensemble``
    ``run_tests`` on in-memory functions - no rootdir discovery, no config
    files, no conftests, no plugin autoload, no capture, no terminal.
``makepyfile``
    Only writes the module, without running anything, so that the file
    materialization cost can be subtracted from the pytester arms.

Each pytester iteration writes a *fresh* module, so it pays assertion
rewriting, compilation and import every time - which is exactly what a
pytester-based test does. The ensemble arm's functions are compiled once,
because an ensemble's sources are plain ``def`` statements in the test body.

Run with::

    python bench/ensemble_vs_pytester.py
    pytest bench/ensemble_vs_pytester.py -s    # equivalent
"""

from __future__ import annotations

from collections.abc import Callable
import contextlib
import io
from pathlib import Path
import time

from _pytest.ensemble import run_tests
from _pytest.pytester import Pytester


#: Number of test functions per run.
SIZES = (1, 10, 100)

#: Iterations per arm. The subprocess arm is orders of magnitude slower, so
#: it gets fewer; the numbers are still stable enough to compare magnitudes.
ITERATIONS = {"subprocess": 3}
DEFAULT_ITERATIONS = 10


def _source(count: int) -> str:
    return "\n".join(f"def test_{i}():\n    assert {i} == {i}" for i in range(count))


def _functions(count: int) -> list[Callable[[], None]]:
    """The in-memory equivalent of :func:`_source`.

    Built once per size, outside the timed loop: an ensemble's sources are
    plain ``def`` statements in the test body, compiled when the test
    module is imported, not materialized per run.
    """
    namespace: dict[str, Callable[[], None]] = {}
    exec(compile(_source(count), "<ensemble-bench>", "exec"), namespace)
    return [namespace[f"test_{i}"] for i in range(count)]


def _files(path: Path) -> int:
    """Files below *path*, ignoring bytecode caches."""
    return sum(
        1
        for p in path.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    )


def _measure(
    run: Callable[[int], None], iterations: int, path: Path
) -> tuple[float, float]:
    """Return (seconds, files created) per iteration.

    Terminal output of the measured runs is redirected away so it does not
    pollute the report; the rendering cost itself is still paid.
    """
    with contextlib.redirect_stdout(io.StringIO()):
        run(0)  # warm up: let lazy imports happen outside the measurement
        before = _files(path)
        start = time.perf_counter()
        for i in range(1, iterations + 1):
            run(i)
        elapsed = time.perf_counter() - start
    return elapsed / iterations, (_files(path) - before) / iterations


def _arms(pytester: Pytester, count: int) -> dict[str, Callable[[int], None]]:
    source = _source(count)
    functions = _functions(count)

    def write(tag: str, i: int) -> str:
        name = f"test_{tag}_{count}_{i}"
        pytester.makepyfile(**{name: source})
        return f"{name}.py"

    def subprocess_(i: int) -> None:
        result = pytester.runpytest_subprocess(write("sub", i))
        assert result.ret == 0, result.outlines

    def inprocess(i: int) -> None:
        result = pytester.runpytest_inprocess(write("inp", i))
        result.assert_outcomes(passed=count)

    def inline(i: int) -> None:
        rec = pytester.inline_run(write("inl", i))
        rec.assertoutcome(passed=count)

    def ensemble(i: int) -> None:
        record = run_tests(*functions, rootpath=pytester.path)
        record.assert_outcomes(passed=count)

    def makepyfile(i: int) -> None:
        write("raw", i)

    return {
        "subprocess": subprocess_,
        "inprocess": inprocess,
        "inline": inline,
        "ensemble": ensemble,
        "makepyfile": makepyfile,
    }


def test_ensemble_vs_pytester(pytester: Pytester) -> None:
    """Run with ``-s`` and read the tables; only the file count is asserted."""
    print()
    by_size: dict[int, dict[str, tuple[float, float]]] = {}
    for count in SIZES:
        results = {}
        for name, run in _arms(pytester, count).items():
            iterations = ITERATIONS.get(name, DEFAULT_ITERATIONS)
            results[name] = _measure(run, iterations, pytester.path)
        by_size[count] = results

        baseline = results["ensemble"][0]
        print(f"\n{count} test function(s) per run")
        print(f"  {'arm':<12} {'per run':>10} {'files':>8} {'vs ensemble':>13}")
        for name, (seconds, files) in results.items():
            ratio = f"{seconds / baseline:.1f}x" if baseline else "n/a"
            print(f"  {name:<12} {seconds * 1000:>8.2f}ms {files:>8.0f} {ratio:>13}")

    # Split the cost in two: what every run pays regardless of size, and
    # what each additional test function adds. A two point estimate over the
    # smallest and largest size is enough to tell the two apart.
    low, high = min(SIZES), max(SIZES)
    print(f"\nfixed cost per run vs marginal cost per test ({low} -> {high} tests)")
    print(f"  {'arm':<12} {'fixed':>10} {'per test':>12}")
    for name in by_size[low]:
        fixed = by_size[low][name][0]
        marginal = (by_size[high][name][0] - fixed) / (high - low)
        print(f"  {name:<12} {fixed * 1000:>8.2f}ms {marginal * 1000:>10.3f}ms")

    print("\n(file counts exclude __pycache__; ensemble writes nothing at all)")

    # The timings are informational, but "no disk at all" is the design claim.
    for count, results in by_size.items():
        assert results["ensemble"][1] == 0, f"ensemble wrote files at size {count}"


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-s", "-q", "-p", "no:randomly"]))
