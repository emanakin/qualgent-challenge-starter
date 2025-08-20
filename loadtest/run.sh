#!/usr/bin/env bash
# Load test runner script
set -euo pipefail

EPISODES=${1:-5}
CONCURRENCY=${2:-2}
PROMPT="${3:-search for load test}"

echo "[loadtest] Starting load test: $CONCURRENCY workers × $EPISODES episodes"
echo "[loadtest] Prompt: '$PROMPT'"

# Ensure we have devices available
if [ ! -f "infra/adb_tunnels.txt" ] || [ ! -s "infra/adb_tunnels.txt" ]; then
    echo "[loadtest] ERROR: No ADB tunnels found. Run ./infra/create_devices.sh first."
    exit 1
fi

AVAILABLE_DEVICES=$(wc -l < infra/adb_tunnels.txt)
echo "[loadtest] Available devices: $AVAILABLE_DEVICES"

if [ "$CONCURRENCY" -gt "$AVAILABLE_DEVICES" ]; then
    echo "[loadtest] WARNING: Requested $CONCURRENCY workers but only $AVAILABLE_DEVICES devices available"
    echo "[loadtest] Consider running: NB_DEVICES=$CONCURRENCY ./infra/create_devices.sh"
fi

# Run the load test
python3 loadtest/stress.py --episodes "$EPISODES" --concurrency "$CONCURRENCY" --prompt "$PROMPT"

echo "[loadtest] Load test completed. Check results/load_test_*.json and results/load_report.md"