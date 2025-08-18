#!/usr/bin/env bash
set -euo pipefail

CONCURRENCY=${1:-5}
EPISODES=${2:-10}

echo "[loadtest] Simulating ${CONCURRENCY} parallel workers * ${EPISODES} episodes"
# In real impl, drive multiple docker runs or runner invocations
