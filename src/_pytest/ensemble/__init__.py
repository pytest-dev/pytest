"""Nested configs and in-memory collection for pytest-under-pytest testing.

EXPERIMENTAL: internal API, no backwards-compatibility guarantees.

A pytest *ensemble* is a deliberately small pytest assembled from parts
handed to it, rather than a full session discovered from a filesystem: a
hermetic nested configuration built from declarative data
(:class:`ConfigSpec`), test items collected from in-memory python objects
instead of files on disk, run through the standard runtest protocol, with
typed report objects to assert on instead of glob-matching rendered
terminal output.

Known limitations (by design, for now):

* Ensembles never load conftest files; pass plugin objects via
  ``ConfigSpec.extra_plugins`` instead.
* The ``capture`` and ``terminal`` plugins are not loaded by default:
  ``capsys``/``capfd`` are unavailable inside an ensemble and no terminal
  output exists. Capture nesting is a planned follow-up.
* Process-global warning filters active around the ensemble (e.g. the
  host suite's ``filterwarnings = error``) are inherited; an ensemble's
  own ``inicfg={"filterwarnings": [...]}`` takes precedence over them.
"""

from __future__ import annotations

from _pytest.ensemble.config import ConfigSpec
from _pytest.ensemble.config import configured
from _pytest.ensemble.config import DEFAULT_PLUGINS


__all__ = [
    "DEFAULT_PLUGINS",
    "ConfigSpec",
    "configured",
]
