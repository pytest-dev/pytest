"""
Called by tox.ini: uses the generated executable to run the tests in ./tests/
directory.
"""

from __future__ import annotations


if __name__ == "__main__":
    import os
    import sys

    executable = os.path.join(os.getcwd(), "dist", "runtests_script", "runtests_script")
    if sys.platform.startswith("win"):
        executable += ".exe"
    sys.exit(os.system(f"{executable} tests"))
