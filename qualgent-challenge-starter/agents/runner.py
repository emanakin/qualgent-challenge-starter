import argparse, json, time, pathlib, random

def run_episode(i: int):
    # TODO: integrate agent-starter-pack + android_world task execution
    # Placeholder result schema
    success = random.random() > 0.2
    return {
        "episode": i,
        "task": "basic_browse",
        "success": success,
        "latency_sec": round(random.uniform(1.0, 5.0), 2),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=5)
    args = parser.parse_args()

    results = []
    for i in range(args.episodes):
        results.append(run_episode(i))

    outdir = pathlib.Path("results")
    outdir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    json_path = outdir / f"results_{ts}.json"
    json_path.write_text(json.dumps(results, indent=2))

    # simple report
    success_rate = sum(1 for r in results if r["success"]) / len(results)
    report = [
        f"# Evaluation Report",
        f"Episodes: {len(results)}",
        f"Success rate: {success_rate:.2%}",
        f"Avg latency (s): {sum(r['latency_sec'] for r in results)/len(results):.2f}",
    ]
    (outdir / "report.md").write_text("\n".join(report))
    print(f"[runner] Wrote: {json_path}")

if __name__ == "__main__":
    main()
