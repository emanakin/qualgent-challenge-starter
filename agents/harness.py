import time
from typing import Dict, Any
from agents.prompt_to_task import plan_from_prompt
from agents.executor import run_task

def run_episode(prompt: str, max_retries: int = 1) -> Dict[str, Any]:
    task, params = plan_from_prompt(prompt)
    attempt = 0
    first_ok = False
    details = ""
    total_latency = 0.0
    res = {}

    while attempt <= max_retries:
        res = run_task(task, params)
        total_latency += res["latency_sec"]
        details = res.get("details", "")
        if res["success"]:
            first_ok = (attempt == 0)
            break
        attempt += 1
        time.sleep(0.5)

    success = res.get("success", False)
    flaky = int(success and not first_ok)
    return {
        "task": task,
        "params": params,
        "success": success,
        "latency_sec": round(total_latency, 3),
        "attempts": attempt + 1,
        "flaky": flaky,
        "details": details[-400:],
    }
