"""
Script used by tox.ini to check the manifest file if we are under version control, or skip the
check altogether if not.

"check-manifest" will needs a vcs to work, which is not available when testing the package
instead of the source code (with ``devpi test`` for example).
"""

from __future__ import print_function

import os
import subprocess
import sys


if os.path.isdir('.git'):
    sys.exit(subprocess.call('check-manifest', shell=True))
else:
    print('No .git directory found, skipping checking the manifest file')
    sys.exit(0)

