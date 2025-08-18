#!/usr/bin/env bash
set -euo pipefail

EPISODES=5
while [[ $# -gt 0 ]]; do
  case "$1" in
    --episodes) EPISODES="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

mkdir -p results
python3 agents/runner.py --episodes "${EPISODES}"
echo "[evaluate] Wrote JSON results to results/ and a short report to results/report.md"
