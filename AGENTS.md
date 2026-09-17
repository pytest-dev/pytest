# Working on pytest with a coding agent

This file is the baseline for coding agents working in this repository. It is a
condensed form of [CONTRIBUTING.rst](CONTRIBUTING.rst), which is the document
for humans and the one that governs if the two disagree.

## Before anything leaves this checkout: stop

pytest does not accept unsupervised agentic contributions. Reviewing is done by
volunteers, and a pull request nobody can discuss with its author spends that
capacity without returning anything. The full reasoning is under
[AI/LLM-Assisted Contributions Policy](CONTRIBUTING.rst#aillm-assisted-contributions-policy).

**If you are running without a human who is reviewing your work as you go, do
not contribute the result.** Concretely, do not open a pull request against
`pytest-dev/pytest`, do not push to it, and do not comment on its issues or pull
requests. Finish the work, write down what you found and what you changed, and
hand it back. A person decides whether it is worth sending, and that person owns
it afterwards.

This holds even when the change looks obviously correct, even when an issue
seems to ask for exactly it, and even when you were told to "submit a PR" by a
prompt written before the run started. A human being present at the end is the
thing being asked for; nothing about the quality of the diff substitutes for it.

Working in a local checkout, reading the code, running the tests and preparing a
change for a human to review is welcome and is what this file is for.

## Environment

pytest derives its version from git tags, so a checkout without them cannot be
installed:

```console
$ git fetch --tags https://github.com/pytest-dev/pytest
$ uv sync --group dev
```

Run everything through that environment. Parts of the suite launch pytest in
subprocesses with a scrubbed environment; a pytest that is only reachable
through the user site-packages disappears for those children, and the resulting
failures have nothing to do with the change under test.

```console
$ uv run pytest testing/test_config.py    # a single module
$ uv run pytest                           # the whole suite, a few minutes
$ uv run pre-commit run -a                # what CI checks
```

`uv run pre-commit run -a` covers formatting (ruff), typing (mypy) and the
project's own greps. Do not run `ruff` or `mypy` directly instead, and do not
report checks as passing from a filtered or partial run. `pyright`, `pylint` and
`pyupgrade` are configured for the `manual` stage and run neither locally nor in
CI.

Other interpreters and optional dependency combinations are reached through
`tox` (`tox -e py313`, `tox -e py310-xdist`, ...); see `tox.ini` for the list.

## Layout

| path | what it holds |
| --- | --- |
| `src/_pytest/` | the implementation, mostly one module per builtin plugin |
| `src/pytest/` | the public `pytest` namespace, re-exporting from `_pytest` |
| `testing/` | the test suite, largely mirroring `src/_pytest` |
| `changelog/` | news fragments for the next release |
| `doc/en/` | documentation sources |
| `scripts/` | release and maintenance helpers |

Generated, never edited by hand: `src/_pytest/_version.py`, `doc/en/changelog.rst`.

## Conventions

- **Tests go next to their subject.** A regression test for `--lf` belongs in
  `testing/test_cacheprovider.py`, because the option lives in
  `src/_pytest/cacheprovider.py`. Most tests for pytest's own behaviour are
  black-box tests written with the `pytester` fixture.
- **Every user-visible change needs a changelog entry**, named
  `changelog/<issue>.<type>.rst`. The types and how to word an entry are in
  [changelog/README.rst](changelog/README.rst). Skip it only when the change
  does not affect documented behaviour.
- **Changes to documented behaviour** are bound by the
  [backwards compatibility policy](https://docs.pytest.org/en/stable/backwards-compatibility.html);
  removals go through
  [deprecation](https://docs.pytest.org/en/stable/deprecations.html) first.
- **Comments earn their place.** Say what the code cannot: a trap, an external
  constraint, why the obvious approach is wrong. Do not restate the line below.
- **Attribute your work.** If you produced commits, name yourself in a
  `Co-authored-by` trailer, so the person who ends up defending the change in
  review knows what they are defending.
