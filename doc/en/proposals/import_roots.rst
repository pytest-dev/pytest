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

Introduce *import roots* as an opt-in alternative to import modes.  Without
import roots configured, pytest behaves exactly as it does today.  With import
roots configured, they replace ``--import-mode`` and the ``pythonpath`` option
entirely; combining either with import roots is a usage error.

An import root declares how one part of the world maps onto the import
system.  There are three kinds:

``local``
    Content that is not distributed (typically the project's own test
    folder).  Modules are imported under the root's declared name, without
    any ``sys.path`` mutation, through an importer pytest installs for the
    duration of the session.  A folder without ``__init__.py`` becomes a
    namespace package whose search path is limited to the root; a folder
    with ``__init__.py`` is imported as a regular package.

``mirrored``
    The worktree source of a distribution that is installed into the current
    environment.  Collection walks the worktree; modules are imported under
    their real, installed name.  pytest classifies the installation (see
    below) and verifies that what it collects is what will be imported.

``installed``
    An installed distribution with no worktree involved.  Collection walks
    the installed files and imports them under their real name, for example
    to run a test suite shipped inside a package.

Conftest files are imported under proper dotted names derived from their
root (``<name>.conftest``, ``<name>.sub.conftest``), removing the need for
``sys.modules`` special-casing.

Configuration
-------------

Import roots are configured in TOML only, as native ``[tool.pytest]`` (or
``pytest.toml``) configuration.  There is no ini spelling.  Every root
requires a ``name``; there is no default and no inference.

.. code-block:: toml

  # contents of pyproject.toml
  [tool.pytest]
  import_roots = [
    { kind = "local", path = "testing", name = "mypkg_testing" },
    { kind = "mirrored", path = "src/mypkg", name = "mypkg" },
    { kind = "installed", name = "otherpkg" },
  ]

``local`` and ``mirrored`` roots take a ``path`` and a ``name``; ``installed``
roots take a ``name`` only.

Conventions and collisions
--------------------------

Import roots rely on conventions and a collision check instead of import
tricks:

* tests that are not shipped live in a top-level ``testing/`` folder,
  declared as a ``local`` root with a project-specific name (for example
  ``mypkg_testing``),
* tests that are shipped live in a ``tests`` subpackage of the package
  (``mypkg/tests/``) and belong to the package's ``mirrored`` or
  ``installed`` root, importing as ``mypkg.tests``,
* a top-level ``tests/`` folder is discouraged under import roots: its name
  does not say which of the two it is, and it is the most common colliding
  top-level name.

When roots are set up, every declared top-level name of a ``local`` root is
checked against ``sys.modules``, the import system (excluding pytest's own
importer) and ``importlib.metadata.packages_distributions()``.  A clash is a
usage error naming the colliding distribution or module.  pytest never
shadows an installed package and is never shadowed by one.

There are no aliases, no path shims and no implicit subprocess support.
Modules of a ``local`` root are importable only inside the pytest process;
code that a subprocess or an unpickler must import belongs in a ``mirrored``
or ``installed`` root.

Interaction with ``testpaths``, ``--pyargs`` and ``pythonpath``
-------------------------------------------------------------------

``testpaths`` and import roots answer different questions and stay separate:
``testpaths`` selects *what* is collected when no arguments are given, import
roots declare *how* collected files are imported.

* every collection target, whether it comes from ``testpaths``, command line
  arguments, or full-tree collection, must fall under exactly one import
  root.  A target outside every root is a usage error.
* ``testpaths`` may point into a ``mirrored`` root (for example
  ``testpaths = ["src"]`` together with ``--doctest-modules``).  Collection
  walks the worktree while imports resolve to the installed name, so the
  staleness verification applies exactly as for test-driven imports.
* ``--pyargs`` arguments are resolved through the configured roots by
  longest name prefix, without importing anything.  The resolved name is
  the name the module is imported under; it is never re-derived from the
  path.  A name matching no root is a usage error.
* ``pythonpath`` is superseded by ``local`` roots.
* conftest files above every root (for example next to ``pyproject.toml``)
  still participate and need a defined module name (see the open
  questions).

Editable versus real versus stale installs
------------------------------------------

For ``mirrored`` roots, pytest performs a minimal classification using
``importlib.metadata`` and :pep:`610` ``direct_url.json``:

editable install
    ``direct_url.json`` marks the distribution as editable.  The worktree
    itself is the import origin, so collection and import trivially agree.
    No content verification is needed.

real (non-editable) install
    The import origin is the installed copy, not the worktree.  pytest
    verifies that the content of each imported file matches the
    corresponding worktree file (for example against the hashes recorded in
    ``RECORD``), and fails collection with a ``StaleInstallError`` (naming
    both paths and suggesting a reinstall) when they differ.  An optional
    strict variant may verify the complete file set of the distribution,
    including files missing on either side.

not installed
    A ``mirrored`` or ``installed`` root whose distribution cannot be found
    fails collection with a clear message, instead of silently falling back
    to path-based importing.

Distributions installed through mechanisms that record no usable provenance
are treated best-effort.

Migration
---------

* Without import roots configured, nothing changes: ``--import-mode``,
  ``--pyargs``, ``pythonpath`` and ``consider_namespace_packages`` behave as
  today.  Import roots are not a new default.
* Configuring import roots together with ``--import-mode`` or ``pythonpath``
  is an error.
* Collection integrates with the directory collection nodes: each collected
  directory belongs to exactly one root, which determines the module names
  beneath it.

Related proposals
-----------------

:doc:`packaged_suites` describes how a test suite shipped inside a package
is declared and bound by a consuming project.  It is independent of import
roots; with roots configured, such a suite's package is an ``installed`` (or
``mirrored``) root.

Open questions
--------------

* the module name for conftest files that live above every import root,
* which file (worktree or installed copy) appears in tracebacks and reports
  for real installs, and how assertion rewriting applies to the installed
  origin,
* the exact TOML schema (field names, validation messages) and the new
  structured option type it needs, since ``addini`` types are currently
  scalar or lists of strings.

Test cases
----------

* no import roots configured: behaviour is identical to today,
* import roots together with ``--import-mode`` or ``pythonpath``: usage
  error,
* a root without ``name``: usage error,
* ``mirrored`` real install: collection succeeds when content matches and
  fails with ``StaleInstallError`` when it differs; strict mode additionally
  detects missing/extra files,
* ``mirrored`` editable install: modules import under the real name with the
  worktree as origin,
* ``mirrored`` or ``installed`` root without a matching distribution:
  collection fails with a clear message,
* ``local`` root without ``__init__.py``: a namespace package anchored at the
  root, with its search path limited to the root,
* ``local`` root with ``__init__.py``: a regular package, still without any
  ``sys.path`` mutation,
* a ``local`` root whose name collides with an installed distribution:
  usage error naming the distribution,
* ``--pyargs`` resolves through roots without importing parents,
* conftest files receive proper dotted module names in every case,
* every collected folder maps to exactly one root.
