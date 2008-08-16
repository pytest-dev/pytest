"""

(DEPRECATED) use py.io.TerminalWriter

"""

import sys, os
import py

py.std.warnings.warn("py.__.misc.terminal_helper is deprecated, use py.io.TerminalWriter", 
                     DeprecationWarning, stacklevel=2)

from py.__.io.terminalwriter import get_terminal_width, terminal_width, ansi_print

