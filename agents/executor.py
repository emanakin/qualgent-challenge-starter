import subprocess, time
from typing import Dict, Any

def _run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out, _ = p.communicate()
    return p.returncode, out or ""

def _adb(args: list[str]) -> tuple[int, str]:
    return _run(["adb", *args])

def _ensure_awake():
    _adb(["shell", "settings", "put", "global", "stay_on_while_plugged_in", "3"])
    _adb(["shell", "input", "keyevent", "26"])
    _adb(["shell", "input", "keyevent", "82"])

def run_task(task: str, params: Dict[str, Any]) -> Dict[str, Any]:
    start = time.time()
    try:
        if task == "browser_search":
            query = params.get("query", "qualgent test")
            _ensure_awake()
            code, out = _adb(["shell", "am", "start",
                               "-a", "android.intent.action.VIEW",
                               "-d", f"https://www.google.com/search?q={query}"])
            ok, details = (code == 0), out[-500:]
        elif task == "open_settings":
            _ensure_awake()
            code, out = _adb(["shell", "am", "start", "-a", "android.settings.SETTINGS"])
            ok, details = (code == 0), out[-500:]
        elif task == "scroll":
            _ensure_awake()
            count = int(params.get("count", 2))
            ok = True; details = ""
            for _ in range(max(1, min(10, count))):
                c, o = _adb(["shell", "input", "swipe", "500", "1600", "500", "600"])  # downwards
                ok = ok and (c == 0)
                time.sleep(0.3)
            details = "scrolled" if ok else "scroll failed"
        elif task == "screenshot":
            _ensure_awake()
            filename = params.get("filename", "shot_1.png")
            # Save to results directory for consistency
            c, o = _run(["bash", "-lc", f"adb exec-out screencap -p > results/{filename}"])
            ok = (c == 0); details = o[-200:]
        elif task == "open_app":
            _ensure_awake()
            pkg = params.get("package", "")
            activity = params.get("activity", "")
            if pkg and activity:
                code, out = _adb(["shell", "am", "start", "-n", f"{pkg}/{activity}"])
            elif pkg:
                code, out = _adb(["shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"])
            else:
                code, out = (1, "missing package")
            ok, details = (code == 0), out[-500:]
        elif task == "open_url":
            _ensure_awake()
            url = params.get("url", "https://www.google.com")
            code, out = _adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url])
            ok, details = (code == 0), out[-500:]
        elif task == "tap":
            _ensure_awake()
            x = str(params.get("x", 500)); y = str(params.get("y", 1000))
            code, out = _adb(["shell", "input", "tap", x, y])
            ok, details = (code == 0), out[-200:]
        elif task == "swipe":
            _ensure_awake()
            x1 = str(params.get("x1", 500)); y1 = str(params.get("y1", 1600))
            x2 = str(params.get("x2", 500)); y2 = str(params.get("y2", 600))
            code, out = _adb(["shell", "input", "swipe", x1, y1, x2, y2])
            ok, details = (code == 0), out[-200:]
        elif task == "type_text":
            _ensure_awake()
            text = params.get("text", "hello world").replace(" ", "%s")
            code, out = _adb(["shell", "input", "text", text])
            ok, details = (code == 0), out[-200:]
        elif task == "nav_home":
            code, out = _adb(["shell", "input", "keyevent", "3"])  # KEYCODE_HOME
            ok, details = (code == 0), out[-100:]
        elif task == "nav_back":
            code, out = _adb(["shell", "input", "keyevent", "4"])  # KEYCODE_BACK
            ok, details = (code == 0), out[-100:]
        elif task == "nav_recents":
            code, out = _adb(["shell", "input", "keyevent", "187"])  # KEYCODE_APP_SWITCH
            ok, details = (code == 0), out[-100:]
        elif task == "open_notifications":
            code, out = _adb(["shell", "cmd", "statusbar", "expand-notifications"])
            ok, details = (code == 0), out[-100:]
        elif task == "wifi":
            enabled = bool(params.get("enabled", True))
            # NOTE: Requires settings context; using cmd for broader support
            state = "enable" if enabled else "disable"
            code, out = _adb(["shell", "svc", "wifi", state])
            ok, details = (code == 0), out[-100:]
        else:
            ok, details = False, f"Unknown task: {task}"
    except Exception as e:
        ok, details = False, f"Exception: {e}"
    latency = round(time.time() - start, 3)
    return {"success": ok, "latency_sec": latency, "task": task, "details": details}
