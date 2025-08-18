# QualGent Challenge — Android Automation Agent (Starter)

This starter gives you a **cloud-first** scaffold to run `android_world` tasks on **Genymotion Cloud** emulators, integrate an **agent** (via Google's `agent-starter-pack` patterns), and ship CI/CD + observability hooks.

## Prereqs (Windows-friendly)
- Windows 10/11 with **WSL2** and **Docker Desktop** (WSL backend)
- A **Genymotion Cloud** account & API key
- (Optional) **Google Cloud** project for Vertex AI & Cloud Logging/Trace
- Git + Python 3.10+ (for helpers)

## Quick start
```bash
# 1) copy and fill your secrets
cp .env.example .env

# 2) (optional) auth to GCP if you plan to use Vertex/observability
# gcloud auth login && gcloud auth application-default login

# 3) create a small emulator pool
./infra/create_devices.sh

# 4) build + run the containerized runner
docker build -t candidate/android-world .
docker run --env-file .env --net=host candidate/android-world

# 5) run N evaluation episodes via the agent harness
./agents/evaluate.sh --episodes 5
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

## Notes
- Scripts are **bash-first**. On Windows, run them from **WSL** (Ubuntu) or translate to PowerShell equivalents in `infra/create_devices.ps1` and `run.ps1` if you prefer.
- The agent pieces are kept intentionally minimal; replace with your implementation as needed.
