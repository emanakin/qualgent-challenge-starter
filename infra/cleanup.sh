#!/usr/bin/env bash
set -euo pipefail
STATE_DIR="$(dirname "$0")"
STATE_FILE="$STATE_DIR/instances.txt"
NAME_PREFIX="${NAME_PREFIX:-qualgent-emu}"

# Collect instance UUIDs either from state file, or fall back to listing by name prefix
collect_instance_ids() {
  local HAVE_FILE_IDS=()
  if [ -s "$STATE_FILE" ]; then
    while IFS= read -r IID; do
      IID="${IID//\r/}"
      [ -n "$IID" ] && HAVE_FILE_IDS+=("$IID")
    done < "$STATE_FILE"
  fi
  if [ ${#HAVE_FILE_IDS[@]} -gt 0 ]; then
    printf '%s\n' "${HAVE_FILE_IDS[@]}"
    return 0
  fi

  # Fallback: discover by prefix from current Genymotion instances
  gmsaas config set output-format json >/dev/null 2>&1 || true
  gmsaas instances list | python3 - "$NAME_PREFIX" <<'PY'
import sys,json,re
prefix=sys.argv[1]
d=json.loads(sys.stdin.read() or '{}')
items=d.get('instances') or d.get('vms') or []
for i in items:
    name=i.get('name') or ''
    if name.startswith(prefix):
        uid=i.get('uuid') or ''
        if uid:
            print(uid)
PY
}

IDS=$(collect_instance_ids | awk 'NF')
if [ -z "$IDS" ]; then
  echo "No instances to clean"
  exit 0
fi

echo "$IDS" | while IFS= read -r IID; do
  echo "[cleanup] Stopping/Deleting $IID"
  STOP_RESULT="$(gmsaas instances stop "$IID" 2>&1 || true)"
  echo "$STOP_RESULT" | sed 's/^/[cleanup][stop] /'
  
  # Check if the instance state is DELETED after stop
  STATE="$(echo "$STOP_RESULT" | grep -o '"state": *"[^"]*"' | head -1 | sed 's/.*"state": *"\([^"]*\)".*/\1/')"
  if [ "$STATE" = "DELETED" ]; then
    echo "[cleanup] $IID successfully deleted"
  else
    echo "[cleanup] $IID state after stop: ${STATE:-unknown}"
    # Try other possible delete commands
    # echo "[cleanup] Attempting alternative deletion methods for $IID"
    # gmsaas instances remove "$IID" 2>/dev/null || true
    # gmsaas instances destroy "$IID" 2>/dev/null || true
    # gmsaas instances terminate "$IID" 2>/dev/null || true
  fi
done

# Best-effort: clear state files
: > "$STATE_FILE" || true
ADB_FILE="$STATE_DIR/adb_tunnels.txt"
: > "$ADB_FILE" || true
