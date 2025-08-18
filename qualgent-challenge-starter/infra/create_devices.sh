#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

: "${GENYMOTION_EMAIL:?Missing GENYMOTION_EMAIL}"
: "${GENYMOTION_API_KEY:?Missing GENYMOTION_API_KEY}"
: "${DEVICE_TEMPLATE:=Pixel_6_12}"
: "${NB_DEVICES:=1}"

echo "[infra] Creating ${NB_DEVICES} Genymotion device(s) using template ${DEVICE_TEMPLATE}"
echo "[infra] NOTE: Replace this script with real API calls or UI steps you document."
# Placeholder: call Genymotion Cloud APIs / CLI here.
# For reviewers, a markdown runbook describing manual UI steps is acceptable.
