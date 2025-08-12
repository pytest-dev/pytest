from __future__ import annotations


__all__ = ["PREAMBLE", "XML_FILE", "__version__", "shtab", "version_tuple"]

try:
    from ._version import version as __version__
    from ._version import version_tuple
except ImportError:  # pragma: no cover
    # broken installation, we don't even try
    # unknown only works because we do poor mans version compare
    __version__ = "unknown"
    version_tuple = (0, 0, "unknown")

try:
    import shtab
except ImportError:
    from . import _shtab as shtab

# https://github.com/iterative/shtab/blob/5358dda86e8ea98bf801a43a24ad73cd9f820c63/examples/customcomplete.py#L11-L22
XML_FILE = {
    "bash": "_shtab_greeter_compgen_xml_files",
    "zsh": "_files -g '*.xml'",
    "tcsh": "f:*.xml",
}
PREAMBLE = {
    "bash": """
# $1=COMP_WORDS[1]
_shtab_greeter_compgen_xml_files() {
  compgen -d -- $1  # recurse into subdirs
  compgen -f -X '!*?.xml' -- $1
}
"""
}
