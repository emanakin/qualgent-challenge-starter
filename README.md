# QualGent Challenge — Android Automation Agent

A production-ready Android automation testing framework with scaling, observability, and reliability features.

## Quick Start

```bash
# 1) Create device pool
./infra/create_devices.sh

# 2) Run evaluation episodes
./evaluate.sh 10 "search for android automation"

# 3) View results
open results/run_*.html  # Rich HTML report
cat results/report.md    # Markdown summary
cat observability/trace_run_*.jsonl  # Detailed traces

# 4) Cleanup
./infra/cleanup.sh
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Genymotion    │    │  Docker Container│    │   Observability │
│   Device Pool   │◄──►│  • Agent Runner  │───►│  • Traces       │
│   (Scalable)    │ADB │  • Executors     │    │  • Metrics      │
│                 │    │  • Health Checks │    │  • Correlation  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Supported Task Prompts

| Category            | Examples                                                             |
| ------------------- | -------------------------------------------------------------------- |
| **Search & Browse** | "search for android automation", "open url https://example.com"      |
| **Navigation**      | "open settings", "open app com.package/.Activity", "go home", "back" |
| **Interaction**     | "tap 500 600", "swipe 500 1600 500 600", "scroll down 3 times"       |
| **Input**           | "type hello world"                                                   |
| **System**          | "wifi on/off", "notifications", "screenshot"                         |

## Observability & Tracing

### Correlation Flow

```
Run ID (run_1234567) ←→ Trace ID (abc123def) ←→ Episodes
├── results/run_1234567.json    # Episode results
├── results/run_1234567.csv     # Tabular data
├── results/run_1234567.html    # Rich report
└── observability/trace_run_1234567.jsonl  # Detailed spans
```

### Trace Structure

```json
{
  "trace_id": "abc123def",
  "run_id": "run_1234567",
  "span": "task.execute",
  "dur_ms": 2340.5,
  "attrs": { "episode": 3, "task": "browser_search" },
  "status": "OK"
}
```

### Google Cloud Integration (Optional)

```bash
export GOOGLE_CLOUD_PROJECT=your-project
export GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
# Traces and logs automatically export to Cloud Logging/Trace
```

## Scaling & Production

### Kubernetes Deployment

```bash
# Deploy runner pods with HPA
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/runner-deployment.yaml
kubectl apply -f k8s/runner-hpa.yaml

# Deploy device pool manager
kubectl apply -f k8s/device-pool-cronjob.yaml

# Scale based on load
kubectl patch hpa android-world-runner-hpa --patch '{"spec":{"maxReplicas":20}}'
```

### Load Testing

```bash
# Test with 3 concurrent workers, 10 episodes each
./loadtest/run.sh 10 3 "search for load test"

# View load test results
cat results/load_report.md
open results/load_test_*.json
```

### Reliability Features

- **Timeouts**: All ADB commands have 5-15s timeouts
- **Health Checks**: Pre-flight ADB connectivity validation
- **Retries**: Automatic retry with flakiness detection
- **Circuit Breaker**: Stops execution if device becomes unresponsive

## CI/CD Pipeline

### GitHub Actions

```bash
# Offline smoke test (always runs)
git push origin main  # Triggers build + test + push

# Online smoke test (optional, requires secrets)
# Set repository variables:
# - ENABLE_ONLINE_SMOKE=true
# - GM_TEMPLATE=53d71621-b0b8-4e5a-8cea-0055ea98988f
# Set repository secrets:
# - GENYMOTION_API_TOKEN=your-token
```

### Local CI Simulation

```bash
# Run offline smoke test
export MOCK_ADB=1
./evaluate.sh 2 "search for ci test"

# Verify no real ADB calls were made
grep "mocked_output" results/run_*.json
```

## Development

### Project Structure

```
├── agents/              # Agent logic & task execution
│   ├── runner.py       # Main evaluation runner with tracing
│   ├── executor.py     # Task executors with timeouts/health checks
│   ├── harness.py      # Episode management & retry logic
│   └── prompt_to_task.py # Natural language → task mapping
├── infra/              # Device pool management
│   ├── create_devices.sh    # Provision Genymotion devices
│   ├── cleanup.sh           # Cleanup device pool
│   └── device_pool_manager.sh # Auto-scaling device pool
├── observability/      # Tracing & monitoring
│   └── trace.py        # JSONL tracer with GCP export
├── loadtest/           # Load & resilience testing
│   ├── stress.py       # Concurrent worker load test
│   └── run.sh          # Load test runner
├── k8s/                # Kubernetes manifests
│   ├── runner-deployment.yaml # Worker pods
│   ├── runner-hpa.yaml        # Horizontal Pod Autoscaler
│   └── device-pool-cronjob.yaml # Device pool manager
└── .github/workflows/  # CI/CD pipeline
    └── ci.yml          # Build, test, push, smoke test
```

### Environment Variables

```bash
# Device connection
ANDROID_SERIAL=localhost:5555    # ADB device target
ADB_HOSTPORT=localhost:5555      # Same as ANDROID_SERIAL

# Genymotion API
GENYMOTION_API_TOKEN=your-token  # API authentication
GM_TEMPLATE=53d71621-...         # Pixel 6 template UUID

# Observability
TRACE_DIR=observability          # Trace output directory
GOOGLE_CLOUD_PROJECT=your-proj   # GCP project for exports

# Testing
MOCK_ADB=1                       # Enable mock mode for CI
```

## Troubleshooting

### Common Issues

```bash
# Device not connecting
adb kill-server && adb start-server
source infra/env.sh && adb connect "$ADB_HOSTPORT"

# Trace files not generated
export TRACE_DIR=observability
mkdir -p observability

# Load test failing
./infra/create_devices.sh  # Ensure enough devices
cat infra/adb_tunnels.txt  # Verify device list

# Health check failing
./healthcheck.sh  # Test ADB connectivity
```

### Performance Tuning

- **Device Pool**: Keep 2-3 warm devices per expected concurrent load
- **Timeouts**: Adjust in `agents/executor.py` based on network latency
- **Resources**: 500m CPU / 512Mi RAM per worker pod recommended
- **Concurrency**: Max stable ~5-10 workers per host (ADB port limits)

## Production Checklist

- [ ] Kubernetes secrets configured (`k8s/secrets.yaml`)
- [ ] HPA limits set appropriately (`k8s/runner-hpa.yaml`)
- [ ] Device pool manager scheduled (`k8s/device-pool-cronjob.yaml`)
- [ ] Load testing completed (`./loadtest/run.sh`)
- [ ] Observability backend configured (GCP/other)
- [ ] CI/CD pipeline validated (`.github/workflows/ci.yml`)
- [ ] Health check endpoints working (`./healthcheck.sh`)

---

**Built for scale, reliability, and observability in production Android testing environments.**
