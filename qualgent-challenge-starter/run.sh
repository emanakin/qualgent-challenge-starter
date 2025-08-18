#!/usr/bin/env bash
set -euo pipefail

# Load env
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

echo "[run] Connecting to Genymotion device pool and verifying ADB..."

# Example: check ADB sees at least one device
adb devices

echo "[run] Installing example APKs if needed (placeholder)"
# adb install /workspace/apks/example.apk || true

echo "[run] Running android_world task(s) (placeholder)"
# Replace with real android_world entrypoint.
python3 - <<'PY'
print("android_world would run here")
PY

echo "[run] Done."
