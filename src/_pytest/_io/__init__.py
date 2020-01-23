# Reexport TerminalWriter from here instead of py, to make it easier to
# extend or swap our own implementation in the future.
from py.io import TerminalWriter as TerminalWriter  # noqa: F401
