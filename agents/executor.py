import subprocess, time, os
from typing import Dict, Any

def _run_with_timeout(cmd: list[str], timeout_sec: float = 15.0) -> tuple[int, str]:
    """Run command with timeout support"""
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        out, _ = p.communicate(timeout=timeout_sec)
        return p.returncode, out or ""
    except subprocess.TimeoutExpired:
        p.kill()
        return 124, "TIMEOUT"
    except Exception as e:
        return 1, f"ERROR: {e}"

def _adb(args: list[str], timeout_sec: float = 15.0) -> tuple[int, str]:
    """ADB command with timeout"""
    # Support mock mode for CI testing
    if os.getenv("MOCK_ADB") == "1":
        return 0, "mocked_output"
    return _run_with_timeout(["adb", *args], timeout_sec)

def adb_healthcheck() -> bool:
    """Check if ADB connection is healthy"""
    code, out = _adb(["get-state"], timeout_sec=5.0)
    return code == 0 and "device" in (out or "").lower()

def _ensure_awake():
    """Wake device and ensure it's unlocked"""
    _adb(["shell", "settings", "put", "global", "stay_on_while_plugged_in", "3"])
    _adb(["shell", "input", "keyevent", "26"])  # Power button
    _adb(["shell", "input", "keyevent", "82"])  # Menu/unlock

def run_task(task: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a task with reliability features"""
    start = time.time()
    
    # Pre-flight healthcheck
    if not adb_healthcheck():
        return {
            "success": False, 
            "latency_sec": 0.0, 
            "task": task, 
            "details": "adb not healthy - device disconnected or unresponsive"
        }
    
    try:
        if task == "browser_search":
            query = params.get("query", "qualgent test")
            _ensure_awake()
            code, out = _adb(["shell", "am", "start",
                               "-a", "android.intent.action.VIEW",
                               "-d", f"https://www.google.com/search?q={query}"], timeout_sec=10.0)
            ok, details = (code == 0), out[-500:]
            
        elif task == "open_settings":
            _ensure_awake()
            code, out = _adb(["shell", "am", "start", "-a", "android.settings.SETTINGS"], timeout_sec=8.0)
            ok, details = (code == 0), out[-500:]
            
        elif task == "scroll":
            _ensure_awake()
            count = int(params.get("count", 2))
            ok = True; details = ""
            for i in range(max(1, min(10, count))):
                c, o = _adb(["shell", "input", "swipe", "500", "1600", "500", "600"], timeout_sec=5.0)
                ok = ok and (c == 0)
                if i < count - 1:  # Don't sleep after last swipe
                    time.sleep(0.3)
            details = f"scrolled {count} times" if ok else "scroll failed"
            
        elif task == "screenshot":
            _ensure_awake()
            filename = params.get("filename", "shot_1.png")
            # Ensure results directory exists
            os.makedirs("results", exist_ok=True)
            c, o = _run_with_timeout(["bash", "-c", f"adb exec-out screencap -p > results/{filename}"], timeout_sec=10.0)
            ok = (c == 0); details = f"saved to results/{filename}" if ok else o[-200:]
            
        elif task == "open_app":
            _ensure_awake()
            pkg = params.get("package", "")
            activity = params.get("activity", "")
            if pkg and activity:
                code, out = _adb(["shell", "am", "start", "-n", f"{pkg}/{activity}"], timeout_sec=8.0)
            elif pkg:
                code, out = _adb(["shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"], timeout_sec=10.0)
            else:
                code, out = (1, "missing package parameter")
            ok, details = (code == 0), out[-500:]
            
        elif task == "open_url":
            _ensure_awake()
            url = params.get("url", "https://www.google.com")
            code, out = _adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url], timeout_sec=10.0)
            ok, details = (code == 0), out[-500:]
            
        elif task == "tap":
            _ensure_awake()
            x = str(params.get("x", 500)); y = str(params.get("y", 1000))
            code, out = _adb(["shell", "input", "tap", x, y], timeout_sec=5.0)
            ok, details = (code == 0), f"tapped ({x},{y})" if code == 0 else out[-200:]
            
        elif task == "swipe":
            _ensure_awake()
            x1 = str(params.get("x1", 500)); y1 = str(params.get("y1", 1600))
            x2 = str(params.get("x2", 500)); y2 = str(params.get("y2", 600))
            code, out = _adb(["shell", "input", "swipe", x1, y1, x2, y2], timeout_sec=5.0)
            ok, details = (code == 0), f"swiped ({x1},{y1})->({x2},{y2})" if code == 0 else out[-200:]
            
        elif task == "type_text":
            _ensure_awake()
            text = params.get("text", "hello world").replace(" ", "%s")
            code, out = _adb(["shell", "input", "text", text], timeout_sec=8.0)
            ok, details = (code == 0), f"typed: {text}" if code == 0 else out[-200:]
            
        elif task == "nav_home":
            code, out = _adb(["shell", "input", "keyevent", "3"], timeout_sec=3.0)  # KEYCODE_HOME
            ok, details = (code == 0), "home pressed" if code == 0 else out[-100:]
            
        elif task == "nav_back":
            code, out = _adb(["shell", "input", "keyevent", "4"], timeout_sec=3.0)  # KEYCODE_BACK
            ok, details = (code == 0), "back pressed" if code == 0 else out[-100:]
            
        elif task == "nav_recents":
            code, out = _adb(["shell", "input", "keyevent", "187"], timeout_sec=3.0)  # KEYCODE_APP_SWITCH
            ok, details = (code == 0), "recents opened" if code == 0 else out[-100:]
            
        elif task == "open_notifications":
            code, out = _adb(["shell", "cmd", "statusbar", "expand-notifications"], timeout_sec=5.0)
            ok, details = (code == 0), "notifications expanded" if code == 0 else out[-100:]
            
        elif task == "wifi":
            enabled = bool(params.get("enabled", True))
            state = "enable" if enabled else "disable"
            code, out = _adb(["shell", "svc", "wifi", state], timeout_sec=5.0)
            ok, details = (code == 0), f"wifi {state}d" if code == 0 else out[-100:]
            
        else:
            ok, details = False, f"Unknown task: {task}"
            
    except Exception as e:
        ok, details = False, f"Exception: {e}"
    
    latency = round(time.time() - start, 3)
    return {
        "success": ok, 
        "latency_sec": latency, 
        "task": task, 
        "details": details,
        "timeout_used": latency > 10.0  # Flag if we likely hit a timeout
    }