"""Utilities for truncating assertion output.

Current default behaviour is to truncate assertion explanations at
terminal lines, unless running with an assertions verbosity level of at least 2 or running on CI.
"""

from __future__ import annotations

from collections.abc import Iterable

from _pytest.assertion._typing import TruncationBudget
from _pytest.compat import running_on_ci
from _pytest.config import Config


DEFAULT_MAX_LINES = 8
DEFAULT_MAX_CHARS = DEFAULT_MAX_LINES * 80
USAGE_MSG = "use '-vv' to show"
TRUNCATION_MSG = f"...Full output truncated, {USAGE_MSG}"

# Truncating appends a footer: ``...`` on the last kept line, a blank line,
# then ``TRUNCATION_MSG``. A body may exceed the raw budget by the footer's
# cost before truncating, so a body that nearly fits is not cut just to
# make room for the footer.
TRUNCATION_FOOTER_LINES = 2  # blank separator + message line
TRUNCATION_FOOTER_CHARS = len("...") + len(TRUNCATION_MSG)


def materialize_with_truncation(lines: Iterable[str], config: Config) -> list[str]:
    """Materialise a streaming explanation, applying truncation lazily.

    Pulls from ``lines`` only until the truncation threshold is reached;
    the rest of the iterator is dropped without being consumed.
    """
    should_truncate, budget = _get_truncation_parameters(config)
    if not should_truncate:
        return list(lines)

    tolerable_max_chars = budget.max_chars + TRUNCATION_FOOTER_CHARS
    # Pull one line past the point where ``_truncate_explanation`` keeps the
    # body whole (``max_lines + TRUNCATION_FOOTER_LINES``) so it can detect the
    # overflow, without us materialising more than we need.
    line_cap = (
        budget.max_lines + TRUNCATION_FOOTER_LINES + 1 if budget.max_lines > 0 else None
    )
    buffered: list[str] = []
    char_count = 0
    for line in lines:
        buffered.append(line)
        char_count += len(line)
        if line_cap is not None and len(buffered) >= line_cap:
            break
        if budget.max_chars > 0 and char_count > tolerable_max_chars:
            break
    else:
        # Iterator exhausted within limits — nothing to truncate.
        return buffered

    return _truncate_explanation(buffered, budget)


def _get_truncation_parameters(config: Config) -> tuple[bool, TruncationBudget]:
    """Return the truncation parameters from the given config, as (should truncate, budget)."""
    # We do not need to truncate if one of conditions is met:
    # 1. Verbosity level is 2 or more;
    # 2. Test is being run in CI environment;
    # 3. Both truncation_limit_lines and truncation_limit_chars
    #    .ini parameters are set to 0 explicitly.
    max_lines = config.getini("truncation_limit_lines")
    max_lines = int(max_lines if max_lines is not None else DEFAULT_MAX_LINES)

    max_chars = config.getini("truncation_limit_chars")
    max_chars = int(max_chars if max_chars is not None else DEFAULT_MAX_CHARS)

    verbose = config.get_verbosity(Config.VERBOSITY_ASSERTIONS)

    should_truncate = verbose < 2 and not running_on_ci()
    should_truncate = should_truncate and (max_lines > 0 or max_chars > 0)

    return should_truncate, TruncationBudget(max_lines=max_lines, max_chars=max_chars)


def _truncate_explanation(
    input_lines: list[str],
    budget: TruncationBudget,
) -> list[str]:
    """Truncate given list of strings that makes up the assertion explanation.

    Truncates to either ``budget.max_lines`` or ``budget.max_chars`` -
    whichever the input reaches first, taking the truncation explanation into
    account. The remaining lines will be replaced by a usage message.

    If max_chars=0, no truncation by character count is performed.
    If max_lines=0, no truncation by line count is performed.

    When this function is launched we know max_lines > 0 or max_chars > 0
    because _get_truncation_parameters was called first.
    """
    # ``max_chars`` bounds the body only; the footer slack is added on top
    # (see ``TRUNCATION_FOOTER_CHARS``).
    tolerable_max_chars = budget.max_chars + TRUNCATION_FOOTER_CHARS
    if (
        budget.max_lines == 0
        or len(input_lines) <= budget.max_lines + TRUNCATION_FOOTER_LINES
    ):
        if (
            budget.max_chars == 0
            or sum(len(s) for s in input_lines) <= tolerable_max_chars
        ):
            return input_lines
        truncated_explanation = input_lines
    else:
        # Truncate first to max_lines, and then truncate to max_chars if necessary
        truncated_explanation = input_lines[: budget.max_lines]
    # We reevaluate the need to truncate chars following removal of some lines
    if (
        budget.max_chars > 0
        and sum(len(e) for e in truncated_explanation) > tolerable_max_chars
    ):
        truncated_explanation = _truncate_by_char_count(
            truncated_explanation, budget.max_chars
        )
    # Something was truncated, adding '...' at the end to show that
    truncated_explanation[-1] += "..."
    return [
        *truncated_explanation,
        "",
        TRUNCATION_MSG,
    ]


def _truncate_by_char_count(input_lines: list[str], max_chars: int) -> list[str]:
    # Find point at which input length exceeds total allowed length
    iterated_char_count = 0
    for iterated_index, input_line in enumerate(input_lines):
        if iterated_char_count + len(input_line) > max_chars:
            break
        iterated_char_count += len(input_line)

    # Create truncated explanation with modified final line
    truncated_result = input_lines[:iterated_index]
    final_line = input_lines[iterated_index]
    if final_line:
        final_line_truncate_point = max_chars - iterated_char_count
        final_line = final_line[:final_line_truncate_point]
    truncated_result.append(final_line)
    return truncated_result
