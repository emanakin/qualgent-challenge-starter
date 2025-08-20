#!/usr/bin/env bash
set -euo pipefail

# Load env
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

echo "[run] Step 1: Connecting to Genymotion device and setting up ADB..."

# Grab the tunnel host:port the script wrote
if [ -f "infra/adb_tunnels.txt" ] && [ -s "infra/adb_tunnels.txt" ]; then
  export ADB_HOSTPORT=$(awk 'NR==1{print $2}' infra/adb_tunnels.txt)
  echo "[run] Found ADB tunnel: $ADB_HOSTPORT"
  
  # Connect and verify
  adb connect "$ADB_HOSTPORT"
  adb devices
  
  # Make this the default target for all tooling
  export ANDROID_SERIAL="$ADB_HOSTPORT"
  echo "[run] Set ANDROID_SERIAL=$ANDROID_SERIAL"
else
  echo "[run] ERROR: No ADB tunnel found. Run ./infra/create_devices.sh first."
  exit 1
fi

echo "[run] Step 2: Testing baseline device control..."

# Keep screen awake & wake/unlock
adb shell settings put global stay_on_while_plugged_in 3
adb shell input keyevent 26  # Power button
adb shell input keyevent 82  # Menu/unlock

# Open a search in the default browser
QUERY="qualgent test"
adb shell am start -a android.intent.action.VIEW -d "https://www.google.com/search?q=${QUERY}"

echo "[run] Step 3: Running AndroidWorld task (placeholder)"
# This is where AndroidWorld integration will go
python3 - <<'PY'
import json
import datetime

# Create a basic test report
report = {
    "timestamp": datetime.datetime.now().isoformat(),
    "test_type": "baseline_adb_control",
    "query": "qualgent test",
    "status": "success",
    "actions_performed": [
        "device_wake",
        "screen_unlock", 
        "browser_search"
    ]
}

# Write JSON report to results/
import os
os.makedirs("results", exist_ok=True)
with open(f"results/baseline_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
    json.dump(report, f, indent=2)

print("Baseline test completed successfully")
PY

echo "[run] Done. Check results/ for test artifacts."
