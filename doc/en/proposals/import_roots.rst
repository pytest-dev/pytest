:orphan:

======================
PROPOSAL: Import roots
======================

.. warning::

    This document outlines a proposal for *import roots*: a declarative
    replacement for the ``--import-mode`` option that aligns test importing
    with the modern Python import system and detects mismatches between the
    worktree and installed distributions.

Problem
-------

pytest currently offers three import modes, none of which is suitable as a
long-term default:

* ``prepend`` and ``append`` permanently mutate ``sys.path``.  They make the
  repository layout dictate importability, allow same-named test modules to
  clash, and silently shadow (or get shadowed by) installed distributions —
  so it is easy to test a different copy of the code than intended.
* ``importlib`` no longer mutates ``sys.path`` and, since pytest 8, imports
  modules under their real name when one can be resolved.  However, when
  resolution fails it falls back to synthetic module names derived from the
  rootdir, and its resolution is *inferred* rather than declared, which keeps
  it surprising in non-trivial layouts.

All three modes share a deeper issue: pytest guesses package roots by walking
up from each file while ``__init__.py`` files are present, anchored on the
rootdir.  This inference is the root cause of a long-standing family of
issues: ``ImportPathMismatchError`` between same-named test trees, conftest
modules being imported twice under different names, and the special-casing
needed to keep unrelated ``conftest`` modules from clobbering each other in
``sys.modules``.

Separately, no mode addresses the dissonance between the worktree and an
installed distribution.  When a project is tested against a non-editable
install (for example in a tox environment), a stale install means tests and
doctests may run against code that differs from the files being collected —
with no diagnostic whatsoever.

Finally, the import machinery that these modes were designed around predates
much of the modern import system.  Python has since standardized:

* namespace packages (:pep:`420`) — packages no longer require
  ``__init__.py``,
* spec-based imports (:pep:`451`) — finders, loaders, and
  ``ModuleSpec`` as the single source of truth for a module's origin,
* recorded install provenance (:pep:`610`) — ``direct_url.json`` marks
  whether a distribution is an editable install,
* standardized editable installs (:pep:`660`),
* ``importlib.metadata`` and ``importlib.resources`` in the standard library
  for interrogating installed distributions and their files.

A modern solution should be expressed in these terms instead of in
``sys.path`` manipulation.

Proposed solution
-----------------

Introduce *import roots* as an alternative to import modes — configuring
import roots replaces ``--import-mode`` entirely rather than adding a fourth
mode.

An import root is a directory in the worktree together with a declaration of
how its content maps onto the import system:

``local``
    Content that is not distributed (typically test folders).  Modules are
    imported under names anchored at the root, without any ``sys.path``
    mutation.  A folder without ``__init__.py`` becomes a namespace package
    whose search path is limited to the root; a folder with ``__init__.py``
    is imported as a regular package.

``installed``
    The worktree source of a distribution that is installed into the current
    environment.  Modules are imported under their real, installed name.
    pytest classifies the installation (see below) and verifies that what it
    collects is what will be imported.

In all cases pytest collects the file tree of the worktree, never touches
``sys.path``, and resolves imports through the standard spec-based machinery.
Conftest files are imported under proper dotted names derived from their
root, removing the need for ``sys.modules`` special-casing.

Implied and explicit roots
--------------------------

pytest should imply import roots automatically in simple cases, so most
projects need no configuration:

* an installed (or editable-installed) distribution whose recorded files map
  back into the worktree implies an ``installed`` root,
* conventional layouts (``src/`` layout, a ``tests`` folder that is not part
  of any distribution) imply their obvious classification.

When the layout is ambiguous — multiple distributions, overlapping trees,
test folders inside installed packages, or content matching no known
distribution — pytest must not guess.  Collection fails with an error that
explains which paths could not be classified and asks for explicit roots:

.. code-block:: ini

  # contents of pytest.ini
  [pytest]
  import_roots =
      tests local
      src/mypkg installed as mypkg

The configuration syntax shown here is a sketch; the concrete spelling
(including a TOML-native form in ``pyproject.toml``) is an open question.

Editable versus real versus stale installs
------------------------------------------

For ``installed`` roots, pytest performs a minimal classification using
``importlib.metadata`` and :pep:`610` ``direct_url.json``:

editable install
    ``direct_url.json`` marks the distribution as editable.  The worktree
    itself is the import origin, so collection and import trivially agree.
    No content verification is needed.

real (non-editable) install
    The import origin is the installed copy, not the worktree.  pytest
    verifies that the content of each imported file matches the
    corresponding worktree file, and fails collection with a
    ``StaleInstallError`` (naming both paths and suggesting a reinstall)
    when they differ.  An optional strict variant may verify the complete
    file set of the distribution, including files missing on either side.

not installed
    A root declared (or implied) as ``installed`` whose distribution cannot
    be found fails collection with a clear message, instead of silently
    falling back to path-based importing.

The detection is deliberately minimal: distributions installed through
mechanisms that record no usable provenance are treated best-effort, with an
explicit root declaration as the escape hatch.

Migration
---------

* Configuring import roots and ``--import-mode`` together is an error.
* The long-term goal is for implied import roots to become pytest's default
  importing behavior, with the legacy import modes deprecated afterwards —
  something none of the existing modes could achieve.
* Collection integrates naturally with the directory collection nodes:
  each collected directory belongs to exactly one root, which determines the
  module names beneath it.

Open questions
--------------

* the concrete configuration syntax (ini line format versus structured TOML),
* interaction with the ``pythonpath`` ini option, ``--pyargs``, and rootdir,
* which file (worktree or installed copy) appears in tracebacks and reports
  for real installs, and how assertion rewriting applies to the installed
  origin,
* how much layout inference is acceptable before requiring explicit roots.

Test cases
----------

* real install: imported name differs from the path in the source tree;
  collection succeeds when content matches and fails with
  ``StaleInstallError`` when it differs; strict mode additionally detects
  missing/extra files,
* editable install: modules import under the real name with the worktree as
  origin,
* declared ``installed`` root without a matching distribution: collection
  fails with a clear message,
* ``local`` root without ``__init__.py``: a namespace package anchored at the
  root, with its search path limited to the root,
* ``local`` root with ``__init__.py``: a regular package, still without any
  ``sys.path`` mutation,
* ambiguous layouts fail collection with a message naming the unclassified
  paths,
* conftest files receive proper dotted module names in every case,
* every collected folder maps to exactly one root.
