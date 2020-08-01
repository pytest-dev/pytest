__all__ = ["__version__"]

import re
from typing import Tuple

try:
    from ._version import version as __version__
except ImportError:
    # broken installation, we don't even try
    # unknown only works because we do poor mans version compare
    __version__ = "unknown"


def version_tuple() -> Tuple[int, int, int, str, str]:
    """
    Return a tuple containing the components of this pytest version:
     (*major*, *minor*, *patch*, *release candidate*, *dev hash*).

    Useful for plugins to handle multiple pytest versions when there are incompatibilities
    at the plugin level, without parsing the version manually.
    """
    return parse_version(__version__)


_VERSION_RE = re.compile(
    r"""
    (?P<major>\d+)
    \.
    (?P<minor>\d+)
    \.
    (?P<patch>\d+)
    (?P<rc>rc\d+)?
    (\.(?P<dev>.*))?
    """,
    re.VERBOSE,
)


def parse_version(version: str) -> Tuple[int, int, int, str, str]:
    m = _VERSION_RE.match(version)
    assert m is not None, "internal error parsing version {}".format(version)
    major = int(m.group("major"))
    minor = int(m.group("minor"))
    patch = int(m.group("patch"))
    rc = m.group("rc") or ""
    dev = m.group("dev") or ""
    return major, minor, patch, rc, dev
