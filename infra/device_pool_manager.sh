#!/usr/bin/env bash
# Device pool manager - ensures N devices are ready for scaling
set -euo pipefail

DESIRED=${1:-1}
GM_TEMPLATE="${GM_TEMPLATE:-53d71621-b0b8-4e5a-8cea-0055ea98988f}"
NAME_PREFIX="${NAME_PREFIX:-pool-runner}"

echo "[pool] Managing device pool: desired=$DESIRED"

# Get current online devices
CURRENT=$(gmsaas instances list 2>/dev/null | grep -c '"state": "ONLINE"' || echo "0")
echo "[pool] Current online devices: $CURRENT"

if [ "$CURRENT" -lt "$DESIRED" ]; then
    NEEDED=$((DESIRED - CURRENT))
    echo "[pool] Scaling up: need $NEEDED more devices"
    
    for i in $(seq 1 $NEEDED); do
        NAME="${NAME_PREFIX}-$(date +%s)-$i"
        echo "[pool] Creating device: $NAME"
        
        # Create device in background to speed up pool creation
        (
            UUID=$(gmsaas instances start "$GM_TEMPLATE" "$NAME" 2>/dev/null | \
                   python3 -c "import sys,json; print(json.load(sys.stdin)['instance']['uuid'])" 2>/dev/null || echo "")
            
            if [ -n "$UUID" ]; then
                echo "[pool] Device $NAME created with UUID: $UUID"
                # Optionally setup ADB tunnel immediately
                gmsaas instances adbconnect "$UUID" >/dev/null 2>&1 || true
            else
                echo "[pool] Failed to create device $NAME"
            fi
        ) &
    done
    
    # Wait for all background jobs
    wait
    echo "[pool] Scale-up completed"

elif [ "$CURRENT" -gt "$DESIRED" ]; then
    EXCESS=$((CURRENT - DESIRED))
    echo "[pool] Scaling down: removing $EXCESS devices"
    
    # Get excess device UUIDs (oldest first)
    EXCESS_UUIDS=$(gmsaas instances list 2>/dev/null | \
                   python3 -c "
import sys, json
data = json.load(sys.stdin)
instances = data.get('instances', [])
online = [i for i in instances if i.get('state') == 'ONLINE']
# Sort by creation time (oldest first)
online.sort(key=lambda x: x.get('created_at', ''))
for i in online[:$EXCESS]:
    print(i.get('uuid', ''))
" 2>/dev/null || echo "")

    for UUID in $EXCESS_UUIDS; do
        if [ -n "$UUID" ]; then
            echo "[pool] Removing device: $UUID"
            gmsaas instances stop "$UUID" >/dev/null 2>&1 || true
            # Note: Genymotion auto-deletes stopped instances after timeout
        fi
    done
    echo "[pool] Scale-down completed"

else
    echo "[pool] Pool size optimal: $CURRENT devices"
fi

echo "[pool] Device pool management finished"
