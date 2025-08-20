import argparse, json, time, pathlib, csv, os, sys
from agents.harness import run_episode

# Add observability path to import tracer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from observability.trace import JsonTracer

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=5)
    ap.add_argument("--prompt", type=str, default="search for qualgent test")
    ap.add_argument("--retries", type=int, default=1)
    args = ap.parse_args()

    outdir = pathlib.Path("results"); outdir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    run_id = f"run_{ts}"
    tracer = JsonTracer(run_id)

    records = []

    with tracer.span("agent.setup", episodes=args.episodes, prompt=args.prompt):
        # Setup phase - check ADB connectivity
        android_serial = os.getenv("ANDROID_SERIAL", "unknown")
        print(f"[runner] Starting {args.episodes} episodes with device {android_serial}")

    for i in range(args.episodes):
        with tracer.span("agent.plan", episode=i, prompt=args.prompt):
            # Planning phase - happens inside run_episode
            pass
        
        t0 = time.time()
        with tracer.span("runner.attach_emulator", episode=i):
            # ADB already connected via evaluate.sh
            pass
        
        with tracer.span("task.execute", episode=i):
            rec = run_episode(args.prompt, max_retries=args.retries)
        
        rec["episode"] = i
        rec["run_id"] = run_id
        rec["trace_id"] = tracer.trace_id
        rec["wall_time_sec"] = round(time.time() - t0, 3)
        records.append(rec)
        print(f"[episode {i}] success={rec['success']} latency={rec['latency_sec']}s flaky={rec['flaky']}")

    # Write JSON results
    json_path = outdir / f"{run_id}.json"
    json_path.write_text(json.dumps(records, indent=2))

    # CSV
    csv_path = outdir / f"{run_id}.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "run_id","episode","task","success","latency_sec","attempts","flaky","trace_id"
        ])
        writer.writeheader()
        for r in records:
            writer.writerow({
                "run_id": r.get("run_id"),
                "episode": r.get("episode"),
                "task": r.get("task"),
                "success": r.get("success"),
                "latency_sec": r.get("latency_sec"),
                "attempts": r.get("attempts"),
                "flaky": r.get("flaky"),
                "trace_id": r.get("trace_id"),
            })

    # Metrics
    successes = [r["success"] for r in records]
    latencies = [r["latency_sec"] for r in records]
    flaky = [r["flaky"] for r in records]
    success_rate = sum(successes) / len(records) if records else 0.0
    avg_time = (sum(latencies) / len(latencies)) if latencies else 0.0
    flakiness = (sum(flaky) / len(records)) if records else 0.0

    # Report (Markdown)
    report_md = outdir / "report.md"
    report_md.write_text("\n".join([
        "# Evaluation Report",
        f"- Run ID: {run_id}",
        f"- Trace ID: {tracer.trace_id}",
        f"- Episodes: {len(records)}",
        f"- Success rate: {success_rate:.2%}",
        f"- Avg latency: {avg_time:.2f}s",
        f"- Flakiness: {flakiness:.2%}",
        "",
        "## Correlation",
        f"- Results file: results/{json_path.name}",
        f"- Trace file: observability/trace_{run_id}.jsonl",
        "- Use run_id + trace_id to correlate spans to each episode."
    ]))

    # Report (HTML)
    rows = []
    for r in records:
        epi = r.get("episode")
        task = r.get("task")
        attempts = r.get("attempts")
        lat = r.get("latency_sec", 0.0)
        ok = r.get("success")
        ok_cell = "<span class=ok>✓</span>" if ok else "<span class=bad>✗</span>"
        rows.append(f"<tr><td>{epi}</td><td>{task}</td><td>{attempts}</td><td>{lat:.2f}</td><td>{ok_cell}</td></tr>")
    rows_html = "".join(rows)

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Evaluation Report - {run_id}</title>
  <style>
    body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 24px; color: #111; }}
    h1 {{ margin-bottom: 0; }}
    .sub {{ color: #555; margin-top: 4px; }}
    .kpi {{ display: flex; gap: 16px; margin: 16px 0; }}
    .card {{ border: 1px solid #eee; border-radius: 8px; padding: 12px 16px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
    th, td {{ border-bottom: 1px solid #eee; text-align: left; padding: 8px; font-size: 14px; }}
    th {{ background: #fafafa; }}
    .ok {{ color: #16803c; font-weight: 600; }}
    .bad {{ color: #9f1239; font-weight: 600; }}
  </style>
</head>
<body>
  <h1>Evaluation Report</h1>
  <div class="sub">Run ID: {run_id} • Trace ID: {tracer.trace_id} • Episodes: {len(records)}</div>
  <div class="kpi">
    <div class="card"><div>Success rate</div><div><strong>{success_rate:.2%}</strong></div></div>
    <div class="card"><div>Avg latency</div><div><strong>{avg_time:.2f}s</strong></div></div>
    <div class="card"><div>Flakiness</div><div><strong>{flakiness:.2%}</strong></div></div>
  </div>
  <table>
    <thead>
      <tr><th>#</th><th>Task</th><th>Attempts</th><th>Latency (s)</th><th>Success</th></tr>
    </thead>
    <tbody>{rows_html}</tbody>
  </table>
  <p><small>Trace file: observability/trace_{run_id}.jsonl</small></p>
</body>
</html>"""
    (outdir / f"{run_id}.html").write_text(html)

    print(f"[runner] wrote {json_path}, {csv_path}, {report_md}, and HTML report (trace in observability/trace_{run_id}.jsonl)")

if __name__ == "__main__":
    main()