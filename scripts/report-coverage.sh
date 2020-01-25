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
# Set --connect-timeout to work around https://github.com/curl/curl/issues/4461
curl -S -L --connect-timeout 5 --retry 6 -s https://codecov.io/bash -o codecov-upload.sh

base_branch="${GITHUB_BASE_REF:-${TRAVIS_BRANCH}}"
base_commit=$(git merge-base FETCH_HEAD "origin/$base_branch")
bash codecov-upload.sh -Z -X fix -f coverage.xml -N "$base_commit" "$@"
