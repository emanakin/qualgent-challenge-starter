#!/usr/bin/env bash
set -euo pipefail

# REQUIREMENTS:
# - gmsaas auth token
# - gmsaas android-sdk-path set
# - adb installed in WSL
# Pixel 6 UUID: 53d71621-b0b8-4e5a-8cea-0055ea98988f

GM_TEMPLATE="${GM_TEMPLATE:-53d71621-b0b8-4e5a-8cea-0055ea98988f}"
NB_DEVICES="${NB_DEVICES:-1}"
NAME_PREFIX="${NAME_PREFIX:-qualgent-emu}"
POLL_TIMEOUT_SEC="${POLL_TIMEOUT_SEC:-300}"
POLL_INTERVAL_SEC="${POLL_INTERVAL_SEC:-5}"

STATE_DIR="$(dirname "$0")"
mkdir -p "$STATE_DIR"
INST_FILE="$STATE_DIR/instances.txt"
ADB_FILE="$STATE_DIR/adb_tunnels.txt"
: > "$INST_FILE"
: > "$ADB_FILE"

gmsaas config set output-format json >/dev/null

json_field() { python3 - "$@" <<'PY'
import sys,json
data=json.loads(sys.stdin.read() or "{}")
path=sys.argv[1:]
for p in path:
    if isinstance(data, dict):
        data = data.get(p, {})
    else:
        data = {}
print(data if isinstance(data,str) else (data if data else ""))
PY
}

list_instances() { gmsaas instances list; }
show_instance()  { gmsaas instances show "$1"; }

uuid_by_name() {
  local NAME="$1"
  list_instances | python3 - "$NAME" <<'PY'
import sys,json
name=sys.argv[1]
d=json.loads(sys.stdin.read() or "{}")
items=d.get("instances") or d.get("vms") or []
for i in items:
    if i.get("name")==name:
        print(i.get("uuid",""))
        break
PY
}

state_by_uuid() {
  local UUID="$1"
  # Since gmsaas instances show doesn't exist, let's check via list and filter by UUID
  gmsaas instances list | python3 - "$UUID" <<'PY'
import sys,json
uuid=sys.argv[1]
d=json.loads(sys.stdin.read() or "{}")
items=d.get("instances") or d.get("vms") or []
for i in items:
    if i.get("uuid")==uuid:
        print(i.get("state") or i.get("status") or "UNKNOWN")
        break
else:
    print("NOT_FOUND")
PY
}

for i in $(seq 1 "$NB_DEVICES"); do
  NAME="${NAME_PREFIX}-${i}"
  echo "[infra] Starting ${NAME} from recipe ${GM_TEMPLATE}..."
  START_JSON="$(gmsaas instances start "$GM_TEMPLATE" "$NAME" 2>&1 || true)"
  echo "$START_JSON" | sed 's/^/[infra][start] /'

  # Extract UUID directly from the JSON output
  UUID="$(echo "$START_JSON" | grep -o '"uuid": *"[^"]*"' | head -1 | sed 's/.*"uuid": *"\([^"]*\)".*/\1/')"
  
  # If that fails, try the json_field function as backup
  if [ -z "$UUID" ]; then
    UUID="$(echo "$START_JSON" | json_field instance uuid)"
  fi
  
  # Final fallback: search by name
  if [ -z "$UUID" ]; then
    for _ in $(seq 1 10); do
      UUID="$(uuid_by_name "$NAME")"
      [ -n "$UUID" ] && break
      sleep 1
    done
  fi
  if [ -z "$UUID" ]; then
    echo "[infra][error] Could not determine UUID for ${NAME}."
    exit 1
  fi
  echo "$UUID" >> "$INST_FILE"
  echo "[infra] ${NAME} => ${UUID}"
  echo "[infra] Written UUID to $INST_FILE"

  # Check if instance is already ONLINE from the start JSON
  INITIAL_STATE="$(echo "$START_JSON" | grep -o '"state": *"[^"]*"' | head -1 | sed 's/.*"state": *"\([^"]*\)".*/\1/')"
  echo "[infra] ${NAME} initial state: ${INITIAL_STATE}"
  
  if [ "$INITIAL_STATE" != "ONLINE" ]; then
    echo "[infra] Waiting for ${NAME} to be ONLINE..."
    SECS=0
    while true; do
      STATE="$(state_by_uuid "$UUID")"
      echo "[infra] ${NAME} state=${STATE:-<unknown>} (${SECS}s)"
      case "$STATE" in ONLINE|RUNNING|ON) break ;; esac
      sleep "$POLL_INTERVAL_SEC"
      SECS=$((SECS + POLL_INTERVAL_SEC))
      if [ "$SECS" -ge "$POLL_TIMEOUT_SEC" ]; then
        echo "[infra][error] Timeout waiting for ${NAME} to be ONLINE. Aborting."
        exit 1
      fi
    done
  else
    echo "[infra] ${NAME} is already ONLINE, proceeding to ADB setup..."
  fi

  echo "[infra] Opening ADB tunnel for ${NAME}..."
  # Ensure adbconnect outputs a host:port; retry briefly if necessary
  HP=""
  for _ in $(seq 1 10); do
    HP="$(gmsaas instances adbconnect "$UUID" | awk '/localhost:[0-9]+/ {print $NF}' | tail -1)"
    # Sanitize: remove quotes, commas, and whitespace
    HP="$(echo "$HP" | sed 's/["\,]//g' | xargs)"
    [ -n "$HP" ] && break
    sleep 1
  done
  if [ -z "$HP" ]; then
    echo "[infra][error] adbconnect did not return a localhost:PORT for ${NAME}."
    exit 1
  fi
  echo "$UUID $HP" >> "$ADB_FILE"
  echo "[infra] ${NAME} ADB at $HP"
  echo "[infra] Written ADB info to $ADB_FILE"
done

echo "[infra] Instances -> $INST_FILE"
echo "[infra] ADB tunnels -> $ADB_FILE"
echo "[infra] Tip: export ADB_HOSTPORT from $ADB_FILE && adb connect \$ADB_HOSTPORT && adb devices"