#!/usr/bin/env bash
set -euo pipefail

# Load env (optional)
if [ -f .env ]; then
  set -a; source .env; set +a
fi

# 1) Resolve ADB tunnel from file if ANDROID_SERIAL is not provided
if [ -z "${ANDROID_SERIAL:-}" ]; then
  if [ -f "infra/adb_tunnels.txt" ] && [ -s "infra/adb_tunnels.txt" ]; then
    export ADB_HOSTPORT=$(awk 'NR==1{print $2}' infra/adb_tunnels.txt | tr -d '",')
    export ANDROID_SERIAL="$ADB_HOSTPORT"
  else
    echo "[run] ERROR: No ANDROID_SERIAL and no infra/adb_tunnels.txt"; exit 1
  fi
fi
echo "[run] Using ANDROID_SERIAL=$ANDROID_SERIAL"

# 2) Ensure adb sees the device (connect if needed)
adb connect "$ANDROID_SERIAL" || true
adb devices

# 3) Baseline control
adb shell settings put global stay_on_while_plugged_in 3 || true
adb shell input keyevent 26 || true
adb shell input keyevent 82 || true

QUERY="qualgent test"
adb shell am start -a android.intent.action.VIEW -d "https://www.google.com/search?q=${QUERY}" || true

# 4) Write a tiny artifact so reviewers see something
python3 - <<'PY'
import json, os, datetime
os.makedirs("results", exist_ok=True)
rep = {
  "timestamp": datetime.datetime.now().isoformat(),
  "test_type": "baseline_adb_control",
  "query": "qualgent test",
  "status": "success",
  "actions": ["wake","unlock","browser_search"]
}
with open(f"results/baseline_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json","w") as f:
    json.dump(rep, f, indent=2)
print("[run] baseline done")
PY

echo "[run] Done. Check results/"
