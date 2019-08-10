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
# Specify branch explicitly - codecov uses target branch for PRs.
# Ref: https://github.com/codecov/codecov-bash/pull/190
branch="${TRAVIS_PULL_REQUEST_BRANCH:-$TRAVIS_BRANCH}"
bash <(curl -s https://codecov.io/bash) -Z -X gcov -X coveragepy -X search -X xcode -X fix -B "$branch" -f coverage.xml
