import argparse, json, time, pathlib, csv
from agents.harness import run_episode

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=5)
    ap.add_argument("--prompt", type=str, default="search for qualgent test")
    ap.add_argument("--retries", type=int, default=1)
    args = ap.parse_args()

    outdir = pathlib.Path("results"); outdir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    run_id = f"run_{ts}"
    records = []

    for i in range(args.episodes):
        rec = run_episode(args.prompt, max_retries=args.retries)
        rec["episode"] = i
        rec["run_id"] = run_id
        records.append(rec)
        print(f"[episode {i}] success={rec['success']} latency={rec['latency_sec']}s flaky={rec['flaky']}")

    # JSON
    (outdir / f"{run_id}.json").write_text(json.dumps(records, indent=2))

    # CSV
    csv_path = outdir / f"{run_id}.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "run_id","episode","task","success","latency_sec","attempts","flaky"
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
            })

    # Metrics
    successes = [r["success"] for r in records]
    latencies = [r["latency_sec"] for r in records]
    flaky = [r["flaky"] for r in records]
    success_rate = sum(successes) / len(records) if records else 0.0
    avg_time = (sum(latencies) / len(latencies)) if latencies else 0.0
    flakiness = (sum(flaky) / len(records)) if records else 0.0

    # Report (Markdown)
    (outdir / "report.md").write_text("\n".join([
        "# Evaluation Report",
        f"- Episodes: {len(records)}",
        f"- Success rate: {success_rate:.2%}",
        f"- Avg latency: {avg_time:.2f}s",
        f"- Flakiness: {flakiness:.2%}",
        f"- Run ID: {run_id}",
    ]))

    # Report (HTML)
    # Build HTML rows safely to avoid quote issues inside f-strings
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

    html = f"""
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
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
    <div class=\"sub\">Run ID: {run_id} • Episodes: {len(records)}</div>
    <div class=\"kpi\">
      <div class=\"card\"><div>Success rate</div><div><strong>{success_rate:.2%}</strong></div></div>
      <div class=\"card\"><div>Avg latency</div><div><strong>{avg_time:.2f}s</strong></div></div>
      <div class=\"card\"><div>Flakiness</div><div><strong>{flakiness:.2%}</strong></div></div>
    </div>
    <table>
      <thead>
        <tr><th>#</th><th>Task</th><th>Attempts</th><th>Latency (s)</th><th>Success</th></tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
  </body>
  </html>
    """
    (outdir / f"{run_id}.html").write_text(html)

if __name__ == "__main__":
    main()
