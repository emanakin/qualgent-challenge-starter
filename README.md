# QualGent Challenge — Android Automation Agent

## Prereqs (Windows-friendly)

- Windows 10/11 with **WSL2** and **Docker Desktop** (WSL backend)
- A **Genymotion Cloud** account & API key
- Git + Python 3.10+ (for helpers)

## Quick start

```bash
# 1) copy and fill your secrets
cp .env.example .env

# 3) create a small emulator pool (writes infra/env.sh)
./infra/create_devices.sh

# (optional) verify ADB locally without Docker
source infra/env.sh
adb connect "$ADB_HOSTPORT"
adb devices

# 4) build + run the containerized runner
docker build -t candidate/android-world .
docker run --rm --net=host \
  -e ANDROID_SERIAL="$ANDROID_SERIAL" \
  -v "$PWD/results:/workspace/results" \
  candidate/android-world

# 5) run N evaluation episodes via the agent harness (non-Docker path)
./evaluate.sh 5 "search for android automation"
```

## Repo layout

```
infra/                # emulator provisioning & device-pool helpers
agents/               # agent adapter + evaluation harness
observability/        # example trace/log export + dashboards
loadtest/             # k6/locust scripts (optional)
results/              # outputs (json/csv) + report.md
Dockerfile            # container for runner + tools
run.sh                # convenience wrapper to attach to emulator and run android_world
README.md             # this file
```

## Supported query prompts (examples)

- "search for qualgent test"
- "open settings"
- "open url https://example.com"
- "open app com.android.settings/.Settings"
- "scroll down 3 times"
- "tap 500 600"
- "swipe 500 1600 500 600"
- "type hello world"
- "go home" / "back" / "recents" / "notifications"
- "wifi on" / "wifi off"

## Notes

- Scripts are **bash-first**. On Windows, run them from **WSL** (Ubuntu) or translate to PowerShell equivalents in `infra/create_devices.ps1` and `run.ps1` if you prefer.
- The agent pieces are kept intentionally minimal; replace with your implementation as needed.
