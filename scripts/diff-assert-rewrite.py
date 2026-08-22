"""Show what assertion rewriting does to a snippet, as a diff.

Each side is one of ``plain`` (the source as written), ``worktree`` (this
checkout's ``src/``) or a released pytest version, which is fetched on demand
with ``uv run --with pytest==VERSION``.  Sides are dumped as rewritten source
(``ast.unparse``) or as an AST, then diffed.

Usage::

    # what rewriting does to a snippet -- plain vs worktree, as source:
    python scripts/diff-assert-rewrite.py -c 'assert (x := f()) and (x := False)'

    # a behaviour change against a release, over a whole file:
    python scripts/diff-assert-rewrite.py --left 8.3.4 testing/example.py

    # same, as AST, when the source form hides the difference:
    python scripts/diff-assert-rewrite.py --left 8.3.4 --format ast -c 'assert a == b'

Exits 1 when the two sides differ, 0 when they do not.
"""

from __future__ import annotations

import argparse
import difflib
import os
from pathlib import Path
import subprocess
import sys
import tempfile


# Runs inside the environment of the pytest version under inspection: reads
# the source file named on its command line, writes the dump to stdout.
_WORKER = """
import ast, sys
fmt, mode, path = sys.argv[1:4]
source = open(path, "rb").read()
tree = ast.parse(source)
if mode == "rewrite":
    from _pytest.assertion.rewrite import rewrite_asserts
    rewrite_asserts(tree, source)
    ast.fix_missing_locations(tree)
print(ast.unparse(tree) if fmt == "source" else ast.dump(tree, indent=2))
"""

_COLORS = {"-": "\033[31m", "+": "\033[32m", "@": "\033[36m"}


def spawn(spec: str, fmt: str, path: Path) -> subprocess.Popen[bytes]:
    """Start the dump of one side -- callers start both, then collect."""
    args = [fmt, "plain" if spec == "plain" else "rewrite", str(path)]
    env = None
    if spec in ("plain", "worktree"):
        cmd = [sys.executable, "-c", _WORKER, *args]
        if spec == "worktree":
            src = Path(__file__).parent.parent / "src"
            env = os.environ | {"PYTHONPATH": str(src)}
    else:
        cmd = ["uv", "run", "--no-project", "--with", f"pytest=={spec}"]
        cmd += ["--", "python", "-c", _WORKER, *args]
    try:
        return subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    except FileNotFoundError as exc:
        raise SystemExit(
            f"{exc.filename} not found (uv: https://docs.astral.sh/uv/)"
        ) from None


def collect(spec: str, proc: subprocess.Popen[bytes]) -> list[str]:
    assert proc.stdout is not None
    out: bytes = proc.stdout.read()
    if proc.wait():
        raise SystemExit(f"dumping {spec} failed")
    return out.decode().splitlines()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "file", type=Path, nargs="?", help="file to rewrite (default: stdin)"
    )
    parser.add_argument("-c", "--code", help="snippet to rewrite instead of a file")
    parser.add_argument(
        "--left",
        default="plain",
        metavar="SPEC",
        help="'plain', 'worktree' or a pytest version",
    )
    parser.add_argument(
        "--right", default="worktree", metavar="SPEC", help="the same, other side"
    )
    parser.add_argument("--format", choices=("source", "ast"), default="source")
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args(argv)

    if args.code is not None:
        source = args.code.encode()
    elif args.file is not None:
        source = args.file.read_bytes()
    else:
        source = sys.stdin.buffer.read()

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp, "snippet.py")
        path.write_bytes(source)
        procs = [
            (side, spawn(side, args.format, path)) for side in (args.left, args.right)
        ]
        left, right = [collect(side, proc) for side, proc in procs]
    diff = list(
        difflib.unified_diff(
            left, right, fromfile=args.left, tofile=args.right, lineterm=""
        )
    )
    if not diff:
        print(f"{args.left} and {args.right} agree on the {args.format} form")
        return

    color = not args.no_color and sys.stdout.isatty()
    for line in diff:
        prefix = _COLORS.get(line[:1], "") if color else ""
        print(f"{prefix}{line}\033[0m" if prefix else line)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
