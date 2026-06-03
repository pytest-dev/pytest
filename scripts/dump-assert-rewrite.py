"""Dump the assert-rewritten form of a Python file for a specific pytest version.

Uses ``uv run`` to execute the rewriter in an ephemeral environment, so any
released pytest version can be inspected without installing it globally.

Usage::

    # Rewritten source (default):
    python scripts/dump-assert-rewrite.py --pytest-version 8.0.0 example.py

    # Using local worktree:
    python scripts/dump-assert-rewrite.py --worktree example.py

    # Compact AST (best for diffing -- no position attributes):
    python scripts/dump-assert-rewrite.py --worktree --format compact example.py

    # Full AST with positions:
    python scripts/dump-assert-rewrite.py --pytest-version 7.4.0 --format ast example.py
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import textwrap


# Self-contained script executed inside the target pytest environment.
# Reads source from stdin, writes the rewritten form to stdout.
_WORKER_SCRIPT = textwrap.dedent("""\
    import ast
    import sys

    source = sys.stdin.buffer.read()
    fmt = sys.argv[1]

    try:
        from _pytest.assertion.rewrite import rewrite_asserts
    except ImportError:
        sys.exit("Could not import rewrite_asserts from this pytest version")

    tree = ast.parse(source)
    try:
        rewrite_asserts(tree, source)
    except TypeError:
        # pytest < 6 did not accept the source parameter
        tree = ast.parse(source)
        rewrite_asserts(tree)

    ast.fix_missing_locations(tree)

    if fmt == "source":
        print(ast.unparse(tree))
    elif fmt == "ast":
        print(ast.dump(tree, indent=2))
    elif fmt == "compact":
        print(ast.dump(tree, indent=2, include_attributes=False))
    else:
        sys.exit(f"Unknown format: {fmt!r}")
""")


def run_worker(
    *,
    pytest_version: str | None,
    worktree: bool,
    file_content: bytes,
    fmt: str,
) -> str:
    """Execute the worker script and return its stdout."""
    if worktree:
        repo_root = Path(__file__).resolve().parent.parent
        env = os.environ.copy()
        env["PYTHONPATH"] = (
            str(repo_root / "src") + os.pathsep + env.get("PYTHONPATH", "")
        )
        cmd = [sys.executable, "-c", _WORKER_SCRIPT, fmt]
    else:
        assert pytest_version is not None
        cmd = [
            "uv",
            "run",
            "--no-project",
            "--with",
            f"pytest=={pytest_version}",
            "--",
            "python",
            "-c",
            _WORKER_SCRIPT,
            fmt,
        ]
        env = None

    try:
        result = subprocess.run(
            cmd, input=file_content, capture_output=True, check=False, env=env
        )
    except FileNotFoundError as exc:
        if "uv" in str(exc):
            raise SystemExit(
                "'uv' not found — install it: https://docs.astral.sh/uv/"
            ) from exc
        raise

    if result.returncode != 0:
        label = version_label(pytest_version=pytest_version, worktree=worktree)
        sys.stderr.buffer.write(result.stderr)
        raise SystemExit(f"Worker failed for {label}")

    return result.stdout.decode()


def version_label(*, pytest_version: str | None = None, worktree: bool = False) -> str:
    """Human-readable label for a pytest source."""
    return "worktree" if worktree else f"pytest=={pytest_version}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "--pytest-version",
        metavar="VER",
        help="Released pytest version (e.g. 8.0.0)",
    )
    src.add_argument(
        "--worktree",
        action="store_true",
        help="Use the local worktree's src/",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=("source", "ast", "compact"),
        default="source",
        help="Output format (default: source)",
    )
    parser.add_argument("file", type=Path, help="Python file to rewrite")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    if not args.file.is_file():
        raise SystemExit(f"File not found: {args.file}")

    output = run_worker(
        pytest_version=args.pytest_version,
        worktree=args.worktree,
        file_content=args.file.read_bytes(),
        fmt=args.fmt,
    )
    sys.stdout.write(output)
    if output and not output.endswith("\n"):
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
