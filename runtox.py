#!/usr/bin/env python

import subprocess
import sys

if __name__ == "__main__":
    subprocess.call(["tox",
                     "-i", "ALL=https://devpi.net/hpk/dev/",
                     "--develop",] + sys.argv[1:])

