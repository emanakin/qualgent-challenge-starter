# observability/trace.py
import json, os, time, uuid, threading, contextlib, sys, datetime
from typing import Optional

TRACE_DIR = os.getenv("TRACE_DIR", "observability")
os.makedirs(TRACE_DIR, exist_ok=True)

# One trace per run_id; correlate with results/<run_id>.json
def new_trace_id() -> str:
    return uuid.uuid4().hex

def _now_ns() -> int:
    return time.time_ns()

class JsonTracer:
    def __init__(self, run_id: str, trace_id: Optional[str] = None):
        self.run_id = run_id
        self.trace_id = trace_id or new_trace_id()
        self.path = os.path.join(TRACE_DIR, f"trace_{self.run_id}.jsonl")
        self._lock = threading.Lock()

    @contextlib.contextmanager
    def span(self, name: str, **attrs):
        start = _now_ns()
        try:
            yield
            status = "OK"
        except Exception as e:
            status = f"ERROR:{e}"
            raise
        finally:
            end = _now_ns()
            rec = {
                "ts": datetime.datetime.utcnow().isoformat() + "Z",
                "run_id": self.run_id,
                "trace_id": self.trace_id,
                "span": name,
                "start_ns": start,
                "end_ns": end,
                "dur_ms": round((end - start) / 1e6, 3),
                "attrs": attrs,
                "status": status,
            }
            with self._lock, open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
            # also emit structured log to stdout for Cloud Logging
            print(json.dumps({"level":"INFO","obs":"span","run_id":self.run_id,"trace_id":self.trace_id,**rec}), flush=True)

# Optional GCP export helper
def export_to_gcp_trace(trace_file: str, project_id: Optional[str] = None):
    """Export JSONL trace to Google Cloud Trace (requires google-cloud-trace)"""
    try:
        from google.cloud import trace_v1
        if not project_id:
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            print("No GCP project configured, skipping trace export")
            return
        
        client = trace_v1.TraceServiceClient()
        # Implementation would parse JSONL and convert to Cloud Trace format
        print(f"Would export {trace_file} to GCP project {project_id}")
    except ImportError:
        print("google-cloud-trace not installed, skipping GCP export")
