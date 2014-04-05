#!/usr/bin/env python

import subprocess
import sys

if __name__ == "__main__":
    subprocess.call([sys.executable, "-m", "tox",
                     "-i", "ALL=https://devpi.net/hpk/dev/",
                     "--develop",] + sys.argv[1:])

