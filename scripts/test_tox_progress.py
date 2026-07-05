"""Tests for tox_progress.py — TDD-driven."""

from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

from tox_progress import build_cmd
from tox_progress import EnvState
from tox_progress import parse_summary_line
from tox_progress import run_env
from tox_progress import strip_ansi
from tox_progress import terminate_all

import pytest


class TestStripAnsi:
    def test_removes_color_codes(self) -> None:
        assert strip_ansi("\033[32mPASSED\033[0m") == "PASSED"

    def test_removes_bold_and_dim(self) -> None:
        assert strip_ansi("\033[1m\033[2mtext\033[0m") == "text"

    def test_preserves_plain_text(self) -> None:
        assert strip_ansi("no ansi here") == "no ansi here"

    def test_removes_multiple_codes(self) -> None:
        assert (
            strip_ansi("\033[31;1mERROR\033[0m: \033[33mwarning\033[0m")
            == "ERROR: warning"
        )


class TestParseSummaryLine:
    def test_parses_real_summary(self) -> None:
        state = EnvState(name="py312")
        result = parse_summary_line(
            "= 100 passed, 5 failed, 10 skipped in 45.2s =", state
        )
        assert result is True
        assert state.passed == 100
        assert state.failed == 5
        assert state.skipped == 10

    def test_parses_summary_with_warnings(self) -> None:
        state = EnvState(name="py312")
        result = parse_summary_line("= 50 passed, 3 warnings in 12.1s =", state)
        assert result is True
        assert state.passed == 50
        assert state.warnings == 3

    def test_rejects_test_output_containing_passed(self) -> None:
        """Test output like 'assert 5 passed validation' should NOT be parsed as summary."""
        state = EnvState(name="py312")
        result = parse_summary_line("assert 5 passed validation checks", state)
        assert result is False
        assert state.passed == 0

    def test_rejects_test_name_with_failed(self) -> None:
        """A test name containing 'failed' should NOT match."""
        state = EnvState(name="py312")
        result = parse_summary_line(
            "testing/test_auth.py::test_3_failed_attempts PASSED", state
        )
        assert result is False
        assert state.failed == 0


class TestRunEnvStdoutCheck:
    def test_raises_runtime_error_when_stdout_is_none(self) -> None:
        """run_env should raise RuntimeError (not AssertionError) when stdout is None."""
        state = EnvState(name="py312")
        mock_proc = MagicMock()
        mock_proc.stdout = None
        with patch("tox_progress.subprocess.Popen", return_value=mock_proc):
            run_env(state, semaphore=None)
        assert state.status == "error"
        # Should NOT be an AssertionError — should be RuntimeError
        assert any(
            "Failed to capture subprocess stdout" in line for line in state.output_lines
        )


class TestBuildCmd:
    def test_plain_pytest_env_has_no_xdist_or_quiet_flags(self) -> None:
        """Non-xdist envs must not get '-n auto' (breaks: no xdist installed)."""
        assert build_cmd("py314") == [
            "uvx",
            "tox",
            "run",
            "-e",
            "py314",
            "--",
            "--no-header",
            "--tb=no",
        ]

    def test_xdist_env_gets_dash_n_auto(self) -> None:
        """Xdist envs must re-request '-n auto' (posargs replace tox's defaults)."""
        assert build_cmd("py314-xdist") == [
            "uvx",
            "tox",
            "run",
            "-e",
            "py314-xdist",
            "--",
            "-n",
            "auto",
            "--no-header",
            "--tb=no",
        ]

    @pytest.mark.parametrize(
        ("env_name", "expect_xdist"),
        [
            ("py310-xdist-coverage", True),
            ("py310-coverage", False),
            ("py310-xdistish", False),
        ],
    )
    def test_xdist_gate_is_token_bounded(
        self, env_name: str, expect_xdist: bool
    ) -> None:
        """Gate must check the 'xdist' dash-token, not a substring match."""
        cmd = build_cmd(env_name)
        has_xdist_flag = "-n" in cmd and "auto" in cmd
        assert has_xdist_flag is expect_xdist

    def test_non_pytest_env_gets_no_posargs(self) -> None:
        """Non-pytest envs (linting, docs, ...) must not get a '--' posargs section."""
        assert build_cmd("linting") == ["uvx", "tox", "run", "-e", "linting"]

    def test_no_quiet_flag_for_any_pytest_env(self) -> None:
        """'-q' suppresses the collection/summary lines the parser depends on."""
        assert "-q" not in build_cmd("py314")
        assert "-q" not in build_cmd("py314-xdist")


class TestTerminateAll:
    def test_terminates_running_proc(self) -> None:
        """A proc still running (poll() returns None) should be terminated."""
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        state = EnvState(name="py312")
        state.proc = mock_proc

        terminate_all([state])

        mock_proc.terminate.assert_called_once()

    def test_does_not_terminate_finished_proc(self) -> None:
        """A proc that has already exited (poll() returns an exit code) is left alone."""
        mock_proc = MagicMock()
        mock_proc.poll.return_value = 0
        state = EnvState(name="py312")
        state.proc = mock_proc

        terminate_all([state])

        mock_proc.terminate.assert_not_called()

    def test_skips_state_with_no_proc(self) -> None:
        """A state whose proc is still None should be skipped without error."""
        state = EnvState(name="py312")

        terminate_all([state])  # must not raise

    def test_terminates_only_running_procs_in_mixed_list(self) -> None:
        """Only the still-running proc in a mixed list gets terminated."""
        running_proc = MagicMock()
        running_proc.poll.return_value = None
        finished_proc = MagicMock()
        finished_proc.poll.return_value = 1

        running_state = EnvState(name="py312")
        running_state.proc = running_proc
        finished_state = EnvState(name="py313")
        finished_state.proc = finished_proc
        none_state = EnvState(name="py314")

        terminate_all([running_state, finished_state, none_state])

        running_proc.terminate.assert_called_once()
        finished_proc.terminate.assert_not_called()

    def test_swallows_process_lookup_error(self) -> None:
        """A terminate() race (process exits between poll and terminate) must not propagate."""
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.terminate.side_effect = ProcessLookupError
        state = EnvState(name="py312")
        state.proc = mock_proc

        terminate_all([state])  # must not raise


class TestSubprocessCleanup:
    def test_proc_stored_on_state_for_cleanup(self) -> None:
        """run_env should store the subprocess on state.proc so callers can terminate it."""
        state = EnvState(name="py312")
        mock_proc = MagicMock()
        mock_proc.stdout = iter(["= 1 passed in 0.1s =\n"])
        mock_proc.wait.return_value = None
        mock_proc.returncode = 0
        with patch("tox_progress.subprocess.Popen", return_value=mock_proc):
            run_env(state, semaphore=None)
        assert state.proc is mock_proc

    def test_proc_is_none_by_default(self) -> None:
        """EnvState should have proc=None before run_env is called."""
        state = EnvState(name="py312")
        assert state.proc is None


class TestShortTestSummaryInfoGuard:
    def test_summary_info_failed_lines_are_not_double_counted(self) -> None:
        """Once 'short test summary info' is seen, live char/word counting for
        that env must stop — otherwise the 'FAILED <nodeid>' recap lines in
        that section re-increment counts already tallied from the live 'F'
        progress characters."""
        state = EnvState(name="py312")
        mock_proc = MagicMock()
        mock_proc.stdout = iter(
            [
                "collected 2 items\n",
                "testing/test_x.py .F\n",
                "=== short test summary info ===\n",
                "FAILED testing/test_x.py::test_b\n",
            ]
        )
        mock_proc.wait.return_value = None
        mock_proc.returncode = 1
        with patch("tox_progress.subprocess.Popen", return_value=mock_proc):
            run_env(state, semaphore=None)
        assert state.failed == 1
