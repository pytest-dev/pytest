"""Show what assertion rewriting does to a snippet, as a diff.

Each side is one of ``plain`` (the source as written), ``worktree`` (this
checkout's ``src/``) or a released pytest version, which is fetched on demand
with ``uv run --with pytest==VERSION``.  Sides are dumped as rewritten source
(``ast.unparse``) or as an AST, then diffed.

Every side runs on one interpreter -- the one running this script, or the one
``--python`` names.  Pin it whenever the comparison is about pytest versions:
an unpinned ``uv run`` is free to pick a different Python for a released
pytest than the worktree runs on, and the grammar differences between the two
then show up in the diff as if the rewriter had changed.

Usage::

    # what rewriting does to a snippet -- plain vs worktree, as source:
    python scripts/diff-assert-rewrite.py -c 'assert (x := f()) and (x := False)'

    # a behaviour change against a release, over a whole file:
    python scripts/diff-assert-rewrite.py --left 8.3.4 testing/example.py

    # same, as AST, when the source form hides the difference:
    python scripts/diff-assert-rewrite.py --left 8.3.4 --format ast -c 'assert a == b'

    # both sides on one interpreter, whatever this script runs on:
    python scripts/diff-assert-rewrite.py --left 8.3.4 --python 3.14 example.py

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


def spawn(
    spec: str, fmt: str, path: Path, python: str | None
) -> subprocess.Popen[bytes]:
    """Start the dump of one side -- callers start both, then collect."""
    args = [fmt, "plain" if spec == "plain" else "rewrite", str(path)]
    repo = Path(__file__).parent.parent
    # src/ ahead of whatever is installed, so 'worktree' means this checkout.
    env = os.environ | {"PYTHONPATH": str(repo / "src")} if spec == "worktree" else None
    if python is None and spec in ("plain", "worktree"):
        cmd = [sys.executable, "-c", _WORKER, *args]
    else:
        cmd = ["uv", "run"]
        if python is not None:
            cmd += ["--python", python]
        # The worktree needs pytest's dependencies; the other sides need none.
        cmd += ["--project", str(repo)] if spec == "worktree" else ["--no-project"]
        if spec not in ("plain", "worktree"):
            cmd += ["--with", f"pytest=={spec}"]
        cmd += ["--", "python", "-c", _WORKER, *args]
    try:
        return subprocess.Popen(
            cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except FileNotFoundError as exc:
        raise SystemExit(
            f"{exc.filename} not found (uv: https://docs.astral.sh/uv/)"
        ) from None


def collect(procs: list[tuple[str, subprocess.Popen[bytes]]]) -> list[list[str]]:
    """Wait for every side before reporting, so no worker outlives the source."""
    done = [(spec, *proc.communicate(), proc.returncode) for spec, proc in procs]
    for spec, _, err, code in done:
        if code:
            sys.stderr.buffer.write(err)
            raise SystemExit(f"dumping {spec} failed")
    return [out.decode().splitlines() for _, out, _, _ in done]


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
    parser.add_argument(
        "--python",
        metavar="X.Y",
        help="run both sides on this Python (default: the current one)",
    )
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
        left, right = collect(
            [
                (side, spawn(side, args.format, path, args.python))
                for side in (args.left, args.right)
            ]
        )
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
