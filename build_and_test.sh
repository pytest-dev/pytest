#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-pytest-env:latest}"
DOCKERFILE_PATH="${1:-${DOCKERFILE_PATH:-Dockerfile}}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

pushd "$SCRIPT_DIR" >/dev/null

docker build -t "$IMAGE_NAME" -f "$DOCKERFILE_PATH" .

docker run --rm "$IMAGE_NAME" bash -lc '
  cd /app && \
  pytest testing && \
  if [ -d .github/workflows/tests ]; then \
    pytest .github/workflows/tests; \
  fi
'

popd >/dev/null
