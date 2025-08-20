#!/usr/bin/env bash
# Health check for ADB connection
set -e

# Check if ADB can see the device
if adb get-state 2>/dev/null | grep -qi device; then
    echo "OK - ADB device connected"
    exit 0
else
    echo "BAD - ADB device not found or not ready"
    exit 1
fi
