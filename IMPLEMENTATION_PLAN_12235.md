# Implementation plan for pytest issue #12235

Issue: [Let `OutcomeException` inherit from `Exception` instead of `BaseException`](https://github.com/pytest-dev/pytest/issues/12235)

Based on local revision `c9c19f8e6` and the issue discussion reviewed on 18 October 2026.

## Scope and rationale

Implement the documentation clarification agreed in the discussion. The maintainer
[opposed changing the superclass](https://github.com/pytest-dev/pytest/issues/12235#issuecomment-2069022098)
because broad `except Exception` handlers could accidentally consume pytest outcomes.
The reporter then requested an explanation in the class docstring, and the maintainer
[welcomed that clarification](https://github.com/pytest-dev/pytest/issues/12235#issuecomment-2069839204).

The current code retains `OutcomeException(BaseException)`, and
`testing/test_runner.py::test_outcomeexception_passes_except_Exception` already
protects its propagation through an `except Exception` handler.

## Implementation steps

1. **Clarify the base-class docstring.** Update `OutcomeException` in
   `src/_pytest/outcomes.py` to explain that these exceptions communicate test and
   collection outcomes to pytest. Explain that inheriting directly from
   `BaseException` lets them propagate through ordinary `except Exception`
   handlers, preserving the intended outcome.

   Proposed wording:

   ```python
   class OutcomeException(BaseException):
       """Indicate a test or collection outcome and contain information about it.

       Inherit from BaseException so that ordinary ``except Exception`` handlers
       do not accidentally suppress pytest outcomes, such as skips, failures,
       and expected failures. These exceptions need to propagate to pytest so
       that it can report the intended outcome.
       """
   ```

2. **Keep the change focused.** Preserve the exception hierarchy, constructors,
   `TEST_OUTCOME`, and outcome handling. The explanation applies to `Skipped`,
   `Failed`, and `XFailed`; avoid implying that `pytest.exit.Exception`, which
   derives from `Exception` separately, has the same inheritance. No public API
   addition or migration is needed.

3. **Reuse existing behavioral coverage.** Run the existing regression test and
   nearby exception-attribute test against the checkout in the project's
   development environment:

   ```text
   python -m pytest testing/test_runner.py::test_outcomeexception_passes_except_Exception testing/test_runner.py::test_outcomeexception_exceptionattributes -q
   pre-commit run --files src/_pytest/outcomes.py
   ```

   No new tests are necessary for this docstring clarification. A Sphinx build
   is only needed if implementation also changes rendered documentation; the
   public API reference does not directly render this internal class docstring.

4. **Review and prepare the patch.** Check that the final diff contains the
   rationale and no runtime changes. Include `changelog/12235.doc.rst` to satisfy
   the PR's changelog check without requiring a maintainer to apply the
   `skip news` exemption label. Suggested PR title:
   `Explain why OutcomeException inherits from BaseException`.

## Acceptance criteria

- The class docstring explains both the inheritance choice and the consequence
  of accidentally suppressing a pytest outcome.
- `OutcomeException` still derives directly from `BaseException`.
- Existing propagation and exception-attribute tests pass; relevant pre-commit
  checks pass.
- The patch remains a documentation clarification with no behavior changes.

## Implementation result

Implemented the docstring clarification on 18 October 2026 and added
`changelog/12235.doc.rst` for the PR's changelog check. The exception hierarchy
and runtime behavior are unchanged.

Validation completed:

- Both targeted tests passed against this checkout, using `PYTHONPATH=src` and
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` to isolate the source from installed pytest
  and third-party plugins.
- `python -m pre_commit run --files src/_pytest/outcomes.py` passed all applicable
  hooks, including Ruff, formatting, spelling, and mypy.
- `git diff --check` passed.
