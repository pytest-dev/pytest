#!/usr/bin/env bash

set -e
set -x

if [ -z "$TOXENV" ]; then
  python -m pip install coverage
else
  # Add last TOXENV to $PATH.
  PATH="$PWD/.tox/${TOXENV##*,}/bin:$PATH"
fi

python -m coverage combine
python -m coverage xml
python -m coverage report -m
bash <(curl -s https://codecov.io/bash) -Z -X gcov -X coveragepy -X search -X xcode -X gcovout -X fix -f coverage.xml
