#!/bin/bash

set -euo pipefail

# Auto Docker rebuild on source changes
# Uses `docker compose watch` if available; otherwise falls back to an `entr` loop.

cd "$(dirname "$0")"

if docker compose help 2>/dev/null | grep -q "watch"; then
  echo "🔁 Using 'docker compose watch' (rebuild on change)"
  docker compose up -d --build
  # This runs in foreground by design to keep watching
  exec docker compose watch
else
  if ! command -v entr >/dev/null 2>&1; then
    echo "⚠️  'entr' not found. Install with: brew install entr"
    exit 1
  fi
  echo "🔁 Using 'entr' fallback watcher (rebuild on change)"
  # Initial build
  docker compose up -d --build
  # Watch all source files except common noisy dirs
  fd -t f -H \
    -E .git -E node_modules -E __pycache__ -E .venv -E venv \
    -E uploads -E exports \
    | entr -r sh -c 'echo "\n♻️  Change detected → rebuilding..." && docker compose build app && docker compose up -d app'
fi
