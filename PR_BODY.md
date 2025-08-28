Summary
Clarifies that `pytest_generate_tests` is uniquely discovered when defined in test modules and classes, while other hooks must reside in `conftest.py` or plugins. Adds brief cross-links for readers and a tiny self-test to demonstrate the behavior.

Motivation
Users can be confused by hook discovery. This highlights the only exception to the “hooks live in conftest/plugins” rule and points to the relevant sections, reducing friction and support questions.

Changes
- `doc/en/how-to/writing_hook_functions.rst`: Add short note about `pytest_generate_tests` special discovery; link to parametrization docs and hook reference.
- `doc/en/how-to/parametrize.rst`: Add short note in the `pytest_generate_tests` section reinforcing the special discovery.
- `testing/test_pytest_generate_tests_discovery.py`: New pytester-based test showing `pytest_generate_tests` in a test module works, while `pytest_terminal_summary` in a test module is not executed.

Tests
- Verifies `pytest_generate_tests` in a test module parametrizes a test (2 passed).
- Verifies another hook (`pytest_terminal_summary`) in a test module is not executed.

Docs
Minimal “Note:” additions with cross-links, kept focused for easy review.

Notes
No behavior change; documentation and a small test only.
Local pre-commit and tests pass; docs build succeeds.

Related Issue
Closes #13577
