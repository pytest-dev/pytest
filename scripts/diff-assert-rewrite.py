"""Compare assert-rewrite output between two pytest versions (or worktree).

Runs the dump script for both sides (in parallel) and shows a unified diff.
Supports all three output formats: source, ast, and compact.

Usage::

    # Two released versions:
    python scripts/diff-assert-rewrite.py --left 7.4.0 --right 8.0.0 example.py

    # Release vs local worktree:
    python scripts/diff-assert-rewrite.py --left 8.3.0 --right worktree example.py

    # Compact AST diff (strips position noise):
    python scripts/diff-assert-rewrite.py --left 7.4.0 --right worktree -f compact example.py

    # All formats at once:
    python scripts/diff-assert-rewrite.py --left 7.4.0 --right 8.0.0 -f all example.py
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import difflib
from pathlib import Path
import sys


_DUMP_SCRIPT = Path(__file__).resolve().parent / "dump-assert-rewrite.py"

_FORMATS = ("source", "ast", "compact")


def _label(spec: str) -> str:
    return "worktree" if spec == "worktree" else f"pytest=={spec}"


def get_dump(spec: str, file_path: Path, fmt: str) -> str:
    """Run the dump script for a single side and return its output."""
    # Import inline so this file stays lightweight at module level.
    import subprocess

    args = [sys.executable, str(_DUMP_SCRIPT)]
    if spec == "worktree":
        args.append("--worktree")
    else:
        args.extend(["--pytest-version", spec])
    args.extend(["--format", fmt, str(file_path)])

    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise SystemExit(f"Dump failed for {_label(spec)}")
    return result.stdout


def colored_diff(lines: list[str]) -> str:
    """Apply ANSI colours to a unified-diff line list."""
    RED = "\033[31m"
    GREEN = "\033[32m"
    CYAN = "\033[36m"
    RESET = "\033[0m"

    out: list[str] = []
    for line in lines:
        if line.startswith(("---", "+++")):
            out.append(f"{CYAN}{line}{RESET}")
        elif line.startswith("-"):
            out.append(f"{RED}{line}{RESET}")
        elif line.startswith("+"):
            out.append(f"{GREEN}{line}{RESET}")
        elif line.startswith("@@"):
            out.append(f"{CYAN}{line}{RESET}")
        else:
            out.append(line)
    return "\n".join(out)


def show_diff(
    left_text: str,
    right_text: str,
    *,
    left_label: str,
    right_label: str,
    fmt: str,
    context: int,
    use_color: bool,
) -> bool:
    """Print a unified diff; return True if differences were found."""
    if left_text == right_text:
        return False

    diff_lines = list(
        difflib.unified_diff(
            left_text.splitlines(),
            right_text.splitlines(),
            fromfile=f"{left_label} [{fmt}]",
            tofile=f"{right_label} [{fmt}]",
            n=context,
        )
    )

    if use_color:
        print(colored_diff(diff_lines))
    else:
        print("\n".join(diff_lines))

    return True


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--left",
        required=True,
        metavar="VER|worktree",
        help="Left side: pytest version or 'worktree'",
    )
    parser.add_argument(
        "--right",
        required=True,
        metavar="VER|worktree",
        help="Right side: pytest version or 'worktree'",
    )
    parser.add_argument(
        "--format",
        "-f",
        dest="fmt",
        choices=(*_FORMATS, "all"),
        default="source",
        help="Output format (default: source)",
    )
    parser.add_argument(
        "--context",
        "-C",
        type=int,
        default=3,
        help="Context lines in diff (default: 3)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable coloured output",
    )
    parser.add_argument("file", type=Path, help="Python file to compare")
    args = parser.parse_args(argv)

    if not args.file.is_file():
        raise SystemExit(f"File not found: {args.file}")

    formats = _FORMATS if args.fmt == "all" else (args.fmt,)
    use_color = not args.no_color and sys.stdout.isatty()
    left_label = _label(args.left)
    right_label = _label(args.right)

    # Fetch all needed dumps in parallel (both sides x all formats).
    jobs: dict[tuple[str, str], str] = {}
    with ThreadPoolExecutor(max_workers=len(formats) * 2) as pool:
        futures = {
            (side, fmt): pool.submit(get_dump, spec, args.file, fmt)
            for fmt in formats
            for side, spec in [("left", args.left), ("right", args.right)]
        }
        for key, future in futures.items():
            jobs[key] = future.result()

    any_diff = False
    for fmt in formats:
        if len(formats) > 1:
            header = f"=== {fmt} ==="
            if use_color:
                header = f"\033[1m{header}\033[0m"
            print(header)

        had_diff = show_diff(
            jobs[("left", fmt)],
            jobs[("right", fmt)],
            left_label=left_label,
            right_label=right_label,
            fmt=fmt,
            context=args.context,
            use_color=use_color,
        )
        if not had_diff:
            print(
                f"No differences in {fmt} output between {left_label} and {right_label}"
            )
        else:
            any_diff = True

        if len(formats) > 1:
            print()

    raise SystemExit(1 if any_diff else 0)


if __name__ == "__main__":
    main()
