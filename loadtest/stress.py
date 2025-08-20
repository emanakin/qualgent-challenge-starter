#!/usr/bin/env python3
"""
Load testing script for Android World agents
Runs multiple workers in parallel, each with its own device
"""

import argparse, subprocess, time, json, pathlib, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any

def run_worker(serial: str, episodes: int, idx: int, prompt: str = "search for load test") -> Dict[str, Any]:
    """Run a single worker against a specific device"""
    env = os.environ.copy()
    env["ANDROID_SERIAL"] = serial
    env["PYTHONPATH"] = "."
    
    t0 = time.time()
    try:
        # Run the agent runner for this worker
        cmd = [
            sys.executable, "agents/runner.py", 
            "--episodes", str(episodes),
            "--prompt", prompt,
            "--retries", "1"
        ]
        
        print(f"[worker-{idx}] Starting {episodes} episodes on {serial}")
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)
        
        duration = time.time() - t0
        success = result.returncode == 0
        
        # Parse results if successful
        episode_results = []
        if success and result.stdout:
            # Extract episode results from stdout
            for line in result.stdout.split('\n'):
                if line.startswith('[episode '):
                    episode_results.append(line.strip())
        
        return {
            "worker": idx,
            "serial": serial,
            "episodes": episodes,
            "success": success,
            "duration_sec": round(duration, 2),
            "returncode": result.returncode,
            "episode_results": episode_results,
            "stdout_tail": result.stdout[-1000:] if result.stdout else "",
            "stderr_tail": result.stderr[-500:] if result.stderr else "",
        }
        
    except subprocess.TimeoutExpired:
        duration = time.time() - t0
        return {
            "worker": idx,
            "serial": serial,
            "episodes": episodes,
            "success": False,
            "duration_sec": round(duration, 2),
            "returncode": -1,
            "episode_results": [],
            "stdout_tail": "TIMEOUT",
            "stderr_tail": "Process timed out after 300s",
        }
    except Exception as e:
        duration = time.time() - t0
        return {
            "worker": idx,
            "serial": serial,
            "episodes": episodes,
            "success": False,
            "duration_sec": round(duration, 2),
            "returncode": -2,
            "episode_results": [],
            "stdout_tail": "",
            "stderr_tail": f"Exception: {e}",
        }

def get_available_devices() -> List[str]:
    """Get list of available ADB devices from tunnel file"""
    tunnel_file = pathlib.Path("infra/adb_tunnels.txt")
    if not tunnel_file.exists():
        print("Error: infra/adb_tunnels.txt not found. Run ./infra/create_devices.sh first.")
        return []
    
    devices = []
    for line in tunnel_file.read_text().splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            # Clean up the host:port (remove quotes/commas)
            host_port = parts[1].strip().strip('",')
            if host_port and "localhost:" in host_port:
                devices.append(host_port)
    
    return devices

def main():
    parser = argparse.ArgumentParser(description="Load test Android World agents")
    parser.add_argument("--episodes", type=int, default=5, help="Episodes per worker")
    parser.add_argument("--concurrency", type=int, default=2, help="Number of concurrent workers")
    parser.add_argument("--prompt", type=str, default="search for load test", help="Prompt for all episodes")
    parser.add_argument("--timeout", type=int, default=600, help="Overall timeout in seconds")
    args = parser.parse_args()

    print(f"Starting load test: {args.concurrency} workers × {args.episodes} episodes")
    
    # Get available devices
    available_devices = get_available_devices()
    if not available_devices:
        print("No devices available. Create devices first with: ./infra/create_devices.sh")
        return 1
    
    # Limit concurrency to available devices
    actual_concurrency = min(args.concurrency, len(available_devices))
    if actual_concurrency < args.concurrency:
        print(f"Warning: Only {len(available_devices)} devices available, limiting to {actual_concurrency} workers")
    
    devices_to_use = available_devices[:actual_concurrency]
    print(f"Using devices: {devices_to_use}")
    
    # Ensure results directory exists
    results_dir = pathlib.Path("results")
    results_dir.mkdir(exist_ok=True)
    
    # Run load test
    start_time = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=actual_concurrency) as executor:
        # Submit all workers
        future_to_idx = {
            executor.submit(run_worker, device, args.episodes, i, args.prompt): i 
            for i, device in enumerate(devices_to_use)
        }
        
        # Collect results as they complete
        try:
            for future in as_completed(future_to_idx, timeout=args.timeout):
                worker_idx = future_to_idx[future]
                try:
                    result = future.result()
                    results.append(result)
                    status = "✓" if result["success"] else "✗"
                    print(f"[worker-{worker_idx}] {status} Completed in {result['duration_sec']}s")
                except Exception as e:
                    print(f"[worker-{worker_idx}] ✗ Exception: {e}")
                    results.append({
                        "worker": worker_idx,
                        "serial": devices_to_use[worker_idx] if worker_idx < len(devices_to_use) else "unknown",
                        "success": False,
                        "duration_sec": 0,
                        "exception": str(e)
                    })
        
        except Exception as e:
            print(f"Load test interrupted: {e}")
    
    total_duration = time.time() - start_time
    
    # Analyze results
    successful_workers = sum(1 for r in results if r.get("success", False))
    total_episodes = sum(r.get("episodes", 0) for r in results)
    avg_worker_duration = sum(r.get("duration_sec", 0) for r in results) / len(results) if results else 0
    
    # Save detailed results
    timestamp = int(time.time())
    load_report = {
        "timestamp": timestamp,
        "test_config": {
            "concurrency": actual_concurrency,
            "episodes_per_worker": args.episodes,
            "total_episodes": total_episodes,
            "prompt": args.prompt,
            "timeout": args.timeout
        },
        "summary": {
            "total_duration_sec": round(total_duration, 2),
            "successful_workers": successful_workers,
            "total_workers": len(results),
            "success_rate": round(successful_workers / len(results), 3) if results else 0,
            "avg_worker_duration_sec": round(avg_worker_duration, 2),
            "episodes_per_second": round(total_episodes / total_duration, 2) if total_duration > 0 else 0
        },
        "worker_results": results,
        "devices_used": devices_to_use
    }
    
    # Write results
    report_file = results_dir / f"load_test_{timestamp}.json"
    report_file.write_text(json.dumps(load_report, indent=2))
    
    # Write summary report
    summary_lines = [
        "# Load Test Report",
        f"**Timestamp:** {timestamp}",
        f"**Test Duration:** {total_duration:.1f}s",
        "",
        "## Configuration",
        f"- Concurrency: {actual_concurrency} workers",
        f"- Episodes per worker: {args.episodes}",
        f"- Total episodes: {total_episodes}",
        f"- Prompt: '{args.prompt}'",
        "",
        "## Results",
        f"- Successful workers: {successful_workers}/{len(results)} ({successful_workers/len(results)*100:.1f}%)",
        f"- Average worker duration: {avg_worker_duration:.1f}s",
        f"- Episodes per second: {total_episodes/total_duration:.2f}",
        "",
        "## Recommendations",
        "- Max stable concurrency: {}".format(actual_concurrency if successful_workers == len(results) else successful_workers),
        "- Typical resource usage: Monitor with `docker stats` or k8s metrics",
        "- Bottlenecks: {}".format("None detected" if successful_workers == len(results) else "Device connectivity or ADB timeouts"),
        "",
        f"**Detailed results:** `{report_file.name}`"
    ]
    
    summary_file = results_dir / "load_report.md"
    summary_file.write_text("\n".join(summary_lines))
    
    # Print summary
    print("\n" + "="*50)
    print("LOAD TEST SUMMARY")
    print("="*50)
    print(f"Workers: {successful_workers}/{len(results)} successful")
    print(f"Duration: {total_duration:.1f}s")
    print(f"Episodes/sec: {total_episodes/total_duration:.2f}")
    print(f"Results saved to: {report_file}")
    print(f"Summary saved to: {summary_file}")
    
    return 0 if successful_workers == len(results) else 1

if __name__ == "__main__":
    exit(main())
