#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
TOPIC="${1:-Adaptive learning rate scheduling for small-batch SGD}"

if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  echo "Missing .venv. Run: python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt" >&2
  exit 1
fi

if [[ ! -f "$ROOT/.env" ]]; then
  echo "Missing .env. Copy .env.example to .env and add an API key." >&2
  exit 1
fi

cd "$ROOT"
exec .venv/bin/python main.py --topic "$TOPIC" --mode loop --rounds 1
