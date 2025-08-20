#!/usr/bin/env bash
set -euo pipefail
EPISODES=${1:-10}
PROMPT="${2:-search for qualgent test}"
RETRIES=${RETRIES:-1}

# Source ADB env if present
if [ -f infra/env.sh ]; then
  # shellcheck disable=SC1091
  source infra/env.sh
fi

# Ensure ADB is connected if env present
if [ -n "${ADB_HOSTPORT:-}" ]; then
  adb connect "$ADB_HOSTPORT" || true
  adb devices | sed 's/^/[evaluate] /'
fi

PYTHONPATH=. python3 agents/runner.py --episodes "$EPISODES" --prompt "$PROMPT" --retries "$RETRIES"
