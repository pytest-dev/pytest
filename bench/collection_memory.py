#!/usr/bin/env python3
"""Measure RSS growth attributable to collecting parametrized items.

Used to track collection memory density (related to issue #619).

Examples::

    python bench/collection_memory.py
    python bench/collection_memory.py --counts 1000,10000,50000,100000
    python bench/collection_memory.py --counts 50000 --json

Reports bytes/item as (RSS after collection - RSS after importing pytest)
divided by the number of collected items. Each count runs in a fresh
subprocess so import/setup costs do not accumulate.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from dataclasses import dataclass
import json
import subprocess
import sys
import tempfile
import textwrap


@dataclass(frozen=True, slots=True)
class CollectionMemoryResult:
    count: int
    items: int
    baseline_rss: int
    after_rss: int
    delta_rss: int
    bytes_per_item: float
    request_deferred: bool
    keywords_markers_is_none: bool
    callspec_marks_type: str
    callspec_argnames: tuple[str, ...]


WORKER = textwrap.dedent(
    r"""
    from __future__ import annotations

    import contextlib
    import gc
    import io
    import sys
    from pathlib import Path

    import pytest

    def rss() -> int:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) * 1024
        return 0

    n = int(sys.argv[1])
    path = Path("bench_param.py")
    path.write_text(
        "import pytest\n\n"
        f'@pytest.mark.parametrize("i", range({n}))\n'
        "def test_it(i):\n"
        "    assert i >= 0\n"
    )

    gc.collect()
    baseline = rss()

    class Plugin:
        def pytest_collection_finish(self, session) -> None:
            self.items = session.items
            item = session.items[0]
            self.request_deferred = item.__dict__.get("_request") is None
            self.keywords_markers_is_none = item.keywords._markers is None
            callspec = item.callspec
            self.callspec_marks_type = type(callspec.marks).__name__
            self.callspec_argnames = callspec._argnames
            gc.collect()
            self.after = rss()

    plugin = Plugin()
    with contextlib.redirect_stdout(io.StringIO()):
        ret = pytest.main(
            ["-q", "--collect-only", "-p", "no:cacheprovider", "--no-header", str(path)],
            plugins=[plugin],
        )
    if ret != 0:
        raise SystemExit(ret)

    items = len(plugin.items)
    delta = plugin.after - baseline
    # Machine-readable one-liner for the parent process.
    print(
        "RESULT",
        items,
        baseline,
        plugin.after,
        delta,
        delta / items,
        int(plugin.request_deferred),
        int(plugin.keywords_markers_is_none),
        plugin.callspec_marks_type,
        ",".join(plugin.callspec_argnames),
        sep="\t",
    )
    """
)


def _run_one(count: int) -> CollectionMemoryResult:
    with tempfile.TemporaryDirectory(prefix="pytest-collection-mem-") as tmp:
        proc = subprocess.run(
            [sys.executable, "-c", WORKER, str(count)],
            capture_output=True,
            text=True,
            cwd=tmp,
            check=False,
        )
    if proc.returncode != 0:
        raise RuntimeError(
            f"worker failed for count={count} (exit {proc.returncode})\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    line = next(ln for ln in proc.stdout.splitlines() if ln.startswith("RESULT\t"))
    (
        _tag,
        items_s,
        baseline_s,
        after_s,
        delta_s,
        per_s,
        req_s,
        kw_s,
        marks_type,
        argnames_s,
    ) = line.split("\t", 9)
    argnames = tuple(a for a in argnames_s.split(",") if a)
    return CollectionMemoryResult(
        count=count,
        items=int(items_s),
        baseline_rss=int(baseline_s),
        after_rss=int(after_s),
        delta_rss=int(delta_s),
        bytes_per_item=float(per_s),
        request_deferred=bool(int(req_s)),
        keywords_markers_is_none=bool(int(kw_s)),
        callspec_marks_type=marks_type,
        callspec_argnames=argnames,
    )


def _parse_counts(value: str) -> list[int]:
    counts = [int(part.strip()) for part in value.split(",") if part.strip()]
    if not counts or any(c <= 0 for c in counts):
        raise argparse.ArgumentTypeError("counts must be positive integers")
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--counts",
        type=_parse_counts,
        default=[1_000, 10_000, 50_000, 100_000],
        help="Comma-separated item counts to measure (default: 1000,10000,50000,100000)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a human-readable table",
    )
    args = parser.parse_args(argv)

    results = [_run_one(count) for count in args.counts]

    if args.json:
        print(json.dumps([asdict(r) for r in results], indent=2))
        return 0

    print(f"python={sys.version.split()[0]} pytest={__import__('pytest').__version__}")
    print(
        f"{'count':>10} {'items':>10} {'Δ MiB':>10} {'B/item':>10} "
        f"{'req deferred':>12} {'kw lazy':>8} {'marks':>8}"
    )
    for r in results:
        print(
            f"{r.count:10d} {r.items:10d} {r.delta_rss / 1024 / 1024:10.1f} "
            f"{r.bytes_per_item:10.0f} {r.request_deferred!s:>12} "
            f"{r.keywords_markers_is_none!s:>8} {r.callspec_marks_type:>8}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
