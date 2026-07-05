#!/usr/bin/env python3
"""Run tox environments in parallel with per-environment progress bars.

Usage:
    python3 tox_progress.py -e linting,py310,py311,py312,py313,py314
    python3 tox_progress.py -e py312,py313 -p 2
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from dataclasses import field
import re
import shutil
import subprocess
import sys
import threading
import time


# ANSI escape helpers
CSI = "\033["
CLEAR_LINE = f"{CSI}2K"
HIDE_CURSOR = f"{CSI}?25l"
SHOW_CURSOR = f"{CSI}?25h"
BOLD = f"{CSI}1m"
RESET = f"{CSI}0m"
GREEN = f"{CSI}32m"
RED = f"{CSI}31m"
YELLOW = f"{CSI}33m"
CYAN = f"{CSI}36m"
DIM = f"{CSI}2m"

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return _ANSI_RE.sub("", text)


@dataclass
class EnvState:
    name: str
    status: str = "pending"  # pending | collecting | running | passed | failed | error
    is_pytest_env: bool = True
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    warnings: int = 0
    current_test: str = ""
    elapsed: float = 0.0
    start_time: float = 0.0
    output_lines: list[str] = field(default_factory=list)
    returncode: int | None = None
    proc: subprocess.Popen[str] | None = None


def parse_collection_line(line: str) -> int | None:
    """Parse 'collected N items' from pytest output."""
    m = re.search(r"collected (\d+) items?", line)
    if m:
        return int(m.group(1))
    return None


def parse_progress_char(line: str, state: EnvState) -> None:
    """Count pytest single-char progress markers (. x s F E etc)."""
    # pytest outputs lines like: "testing/test_foo.py .....x..F.s"
    # or in verbose mode: "testing/test_foo.py::test_bar PASSED"
    # Also handles percentage output like: "testing/test_foo.py ...... [ 10%]"

    # Strip ANSI codes for parsing
    clean = strip_ansi(line)

    # Verbose mode: "PASSED", "FAILED", "ERROR", "SKIPPED"
    if re.search(r"\bPASSED\b", clean):
        state.passed += 1
        return
    if re.search(r"\bFAILED\b", clean):
        state.failed += 1
        return
    if re.search(r"\bERROR\b", clean):
        state.errors += 1
        return
    if re.search(r"\bSKIPPED\b", clean):
        state.skipped += 1
        return

    # Count progress chars from lines like:
    #   "testing/test_foo.py .....xsF"           (non-xdist)
    #   "testing/test_foo.py .....xsF  [ 45%]"   (non-xdist with pct)
    #   ".....xsF"                                (xdist, no file prefix)
    #   "......x....  [ 66%]"                     (xdist with pct)
    # Extract the progress chars, optionally preceded by a file path
    m = re.match(r"^(?:\S+\.py\s+)?([.xXsFE]+)(?:\s+\[\s*\d+%\])?\s*$", clean)
    if m:
        chars = m.group(1)
        for c in chars:
            if c == ".":
                state.passed += 1
            elif c == "F":
                state.failed += 1
            elif c == "E":
                state.errors += 1
            elif c in ("x", "X", "s"):
                state.skipped += 1
        return


NON_PYTEST_ENVS = {
    "linting",
    "docs",
    "docs-checklinks",
    "regen",
    "release",
    "prepare-release-pr",
    "generate-gh-release-notes",
    "update-plugin-list",
}


def build_cmd(env_name: str) -> list[str]:
    """Build the tox invocation for a single environment.

    Pytest envs get '--no-header --tb=no' posargs (never '-q': it silences the
    'collected N items' line and the '='-delimited summary this script's
    parser depends on). xdist envs additionally re-request '-n auto' — tox
    posargs REPLACE the env's default posargs, so pytest-xdist parallelism
    must be re-fed explicitly. Only envs whose name has an 'xdist' dash-token
    (not merely an 'xdist' substring) get it.
    """
    cmd = ["uvx", "tox", "run", "-e", env_name]
    if env_name in NON_PYTEST_ENVS:
        return cmd
    posargs = []
    if "xdist" in env_name.split("-"):
        posargs += ["-n", "auto"]
    posargs += ["--no-header", "--tb=no"]
    return [*cmd, "--", *posargs]


def parse_summary_line(line: str, state: EnvState) -> bool:
    """Parse the final summary line like '= 1234 passed, 5 failed in 45.2s ='."""
    clean = strip_ansi(line)
    # pytest summary lines are delimited by '=' and end with 'in X.Xs ='
    if not re.search(r"=.*\bin\s+[\d.]+s\s*=", clean):
        return False
    m_passed = re.search(r"(\d+) passed", clean)
    m_failed = re.search(r"(\d+) failed", clean)
    m_error = re.search(r"(\d+) error", clean)
    m_skipped = re.search(r"(\d+) skipped", clean)
    m_warnings = re.search(r"(\d+) warning", clean)
    if not any((m_passed, m_failed, m_error)):
        return False
    if m_passed:
        state.passed = int(m_passed.group(1))
    if m_failed:
        state.failed = int(m_failed.group(1))
    if m_error:
        state.errors = int(m_error.group(1))
    if m_skipped:
        state.skipped = int(m_skipped.group(1))
    if m_warnings:
        state.warnings = int(m_warnings.group(1))
    return True


def run_env(state: EnvState, semaphore: threading.Semaphore | None) -> None:
    """Run a single tox environment and track progress."""
    if semaphore:
        semaphore.acquire()

    state.status = "collecting"
    state.start_time = time.time()

    # Only pass pytest flags to environments that actually run pytest
    non_pytest_envs = {
        "linting",
        "docs",
        "docs-checklinks",
        "regen",
        "release",
        "prepare-release-pr",
        "generate-gh-release-notes",
        "update-plugin-list",
    }
    is_pytest_env = state.name not in non_pytest_envs
    state.is_pytest_env = is_pytest_env

    if not is_pytest_env:
        state.status = "running"

    try:
        cmd = build_cmd(state.name)
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        # Expose the process so callers can terminate it (e.g. on Ctrl-C).
        state.proc = proc

        if proc.stdout is None:
            raise RuntimeError("Failed to capture subprocess stdout")
        in_short_summary = False
        for raw_line in proc.stdout:
            line = raw_line.rstrip("\n")
            state.output_lines.append(line)
            state.elapsed = time.time() - state.start_time

            # xdist: detect worker startup
            clean_check = strip_ansi(line)
            if "bringing up nodes" in clean_check:
                state.status = "collecting"
                continue

            # Check for collection count
            n = parse_collection_line(line)
            if n is not None:
                state.total = n
                state.status = "running"
                continue

            # Check for final summary
            if parse_summary_line(line, state):
                continue

            # pytest's "short test summary info" recap re-lists each failure
            # (e.g. "FAILED testing/test_x.py::test_b"). Those lines must not
            # be re-counted on top of the live progress chars that already
            # tallied them, so stop char/word counting once we're in it.
            if "short test summary info" in clean_check:
                in_short_summary = True

            # Track progress chars
            if state.status == "running" and not in_short_summary:
                parse_progress_char(line, state)

            # Track current file being tested
            clean = strip_ansi(line)
            m = re.match(r"^(testing/\S+\.py|doc/\S+\.py)", clean)
            if m:
                state.current_test = m.group(1)

        proc.wait()
        state.returncode = proc.returncode
        state.elapsed = time.time() - state.start_time

        if state.returncode == 0:
            state.status = "passed"
        else:
            state.status = "failed"

    except Exception as e:
        state.status = "error"
        state.output_lines.append(f"ERROR: {e}")
    finally:
        if semaphore:
            semaphore.release()


def format_bar(state: EnvState, width: int) -> str:
    """Format a single progress bar line."""
    name_w = 10
    name = state.name.ljust(name_w)

    elapsed_str = f"{state.elapsed:5.0f}s" if state.elapsed > 0 else "    -"

    done = state.passed + state.failed + state.errors + state.skipped
    total = state.total if state.total > 0 else done

    if state.status == "pending":
        return f"  {DIM}{name}  ⏳ waiting{RESET}"

    if state.status == "collecting":
        return (
            f"  {CYAN}{name}  📦 collecting tests...{RESET}  {DIM}{elapsed_str}{RESET}"
        )

    if not state.is_pytest_env and state.status == "running":
        # Non-pytest envs (linting, docs, etc.) - show a spinner
        spinner = "⣾⣽⣻⢿⡿⣟⣯⣷"
        frame = spinner[int(state.elapsed * 3) % len(spinner)]
        return f"  {CYAN}{name}  {frame} running...{RESET}  {DIM}{elapsed_str}{RESET}"

    if state.status in ("passed", "failed", "error"):
        if state.status == "passed":
            icon = f"{GREEN}✅ PASSED{RESET}"
        elif state.status == "failed":
            icon = f"{RED}❌ FAILED{RESET}"
        else:
            icon = f"{RED}💥 ERROR{RESET}"

        parts = []
        if state.passed:
            parts.append(f"{GREEN}{state.passed} passed{RESET}")
        if state.failed:
            parts.append(f"{RED}{state.failed} failed{RESET}")
        if state.errors:
            parts.append(f"{RED}{state.errors} errors{RESET}")
        if state.skipped:
            parts.append(f"{DIM}{state.skipped} skipped{RESET}")
        summary = ", ".join(parts) if parts else ""

        return f"  {name}  {icon}  {summary}  {DIM}{elapsed_str}{RESET}"

    # Running state - show progress bar
    pct = (done / total * 100) if total > 0 else 0
    bar_total_w = max(width - name_w - 40, 10)
    filled = int(bar_total_w * done / total) if total > 0 else 0
    empty = bar_total_w - filled

    # Color the bar based on failures
    bar_color = GREEN if state.failed == 0 and state.errors == 0 else YELLOW
    bar = f"{bar_color}{'█' * filled}{DIM}{'░' * empty}{RESET}"

    counts = f"{done}/{total}"
    fail_str = f" {RED}{state.failed}F{RESET}" if state.failed else ""
    err_str = f" {RED}{state.errors}E{RESET}" if state.errors else ""

    return f"  {CYAN}{name}{RESET}  {bar}  {pct:5.1f}%  {counts}{fail_str}{err_str}  {DIM}{elapsed_str}{RESET}"


def render_display(states: list[EnvState], term_width: int) -> str:
    """Render the full display."""
    lines: list[str] = []
    lines.append(f"\n  {BOLD}tox parallel runner{RESET}")
    lines.append(f"  {'─' * (term_width - 4)}")

    for s in states:
        lines.append(format_bar(s, term_width))

    lines.append(f"  {'─' * (term_width - 4)}")

    # Overall summary
    running = sum(1 for s in states if s.status in ("collecting", "running"))
    done = sum(1 for s in states if s.status in ("passed", "failed", "error"))
    total = len(states)
    lines.append(f"  {done}/{total} complete, {running} running")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run tox with progress bars")
    parser.add_argument(
        "-e", "--envs", required=True, help="Comma-separated tox environments"
    )
    parser.add_argument(
        "-p", "--parallel", type=int, default=0, help="Max parallel jobs (0=all)"
    )
    args = parser.parse_args()

    env_names = [e.strip() for e in args.envs.split(",") if e.strip()]
    states = [EnvState(name=name) for name in env_names]

    semaphore = threading.Semaphore(args.parallel) if args.parallel > 0 else None

    threads: list[threading.Thread] = []
    for state in states:
        t = threading.Thread(target=run_env, args=(state, semaphore), daemon=True)
        threads.append(t)

    term_width = shutil.get_terminal_size().columns
    num_display_lines = 0

    print(HIDE_CURSOR, end="", flush=True)

    try:
        for t in threads:
            t.start()

        while any(t.is_alive() for t in threads):
            # Move cursor up to overwrite previous display
            if num_display_lines > 0:
                print(f"{CSI}{num_display_lines}A", end="")

            output = render_display(states, term_width)
            display_lines = output.split("\n")
            num_display_lines = len(display_lines)

            for line in display_lines:
                print(f"{CLEAR_LINE}{line}")

            sys.stdout.flush()
            time.sleep(0.3)

        # Final render
        if num_display_lines > 0:
            print(f"{CSI}{num_display_lines}A", end="")
        output = render_display(states, term_width)
        for line in output.split("\n"):
            print(f"{CLEAR_LINE}{line}")
        print()

    finally:
        print(SHOW_CURSOR, end="", flush=True)

    # Print failures
    failed_states = [s for s in states if s.status in ("failed", "error")]
    if failed_states:
        print(f"\n{RED}{BOLD}Failures:{RESET}")
        for s in failed_states:
            print(f"\n  {RED}── {s.name} ──{RESET}")
            # Print last 30 lines of output for context
            tail = s.output_lines[-30:]
            for line in tail:
                print(f"    {line}")

    return 1 if failed_states else 0


if __name__ == "__main__":
    sys.exit(main())
