"""Tests for tox_progress.py — TDD-driven."""

from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

from tox_progress import EnvState
from tox_progress import parse_summary_line
from tox_progress import run_env
from tox_progress import strip_ansi


class TestStripAnsi:
    def test_removes_color_codes(self) -> None:
        assert strip_ansi("\033[32mPASSED\033[0m") == "PASSED"

    def test_removes_bold_and_dim(self) -> None:
        assert strip_ansi("\033[1m\033[2mtext\033[0m") == "text"

    def test_preserves_plain_text(self) -> None:
        assert strip_ansi("no ansi here") == "no ansi here"

    def test_removes_multiple_codes(self) -> None:
        assert strip_ansi("\033[31;1mERROR\033[0m: \033[33mwarning\033[0m") == "ERROR: warning"


class TestParseSummaryLine:
    def test_parses_real_summary(self) -> None:
        state = EnvState(name="py312")
        result = parse_summary_line("= 100 passed, 5 failed, 10 skipped in 45.2s =", state)
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
        result = parse_summary_line("testing/test_auth.py::test_3_failed_attempts PASSED", state)
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
        assert any("Failed to capture subprocess stdout" in line for line in state.output_lines)


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