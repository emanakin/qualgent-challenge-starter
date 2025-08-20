from typing import Dict, Any, Tuple
import re

DEFAULT_TASK = ("browser_search", {"query": "qualgent test"})

def plan_from_prompt(prompt: str) -> Tuple[str, Dict[str, Any]]:
    p = (prompt or "").lower()
    if "search" in p or "browse" in p or "google" in p:
        parts = p.split("search for ")
        query = parts[1].strip() if len(parts) > 1 else "qualgent test"
        return ("browser_search", {"query": query[:100]})
    if "open settings" in p:
        return ("open_settings", {})
    if "scroll" in p:
        # e.g., "scroll down 3 times"
        count = 2
        for tok in p.split():
            if tok.isdigit():
                count = max(1, min(10, int(tok)))
                break
        return ("scroll", {"direction": "down", "count": count})
    if "screenshot" in p:
        return ("screenshot", {"filename": "shot_1.png"})

    # Open a specific app/activity: "open app com.foo/.MainActivity"
    if p.startswith("open app "):
        rest = prompt.split(" ", 2)[2].strip()
        pkg = rest
        activity = ""
        if "/" in rest:
            pkg, activity = rest.split("/", 1)
        return ("open_app", {"package": pkg.strip(), "activity": activity.strip()})

    # Open a URL directly: "open url https://example.com"
    if p.startswith("open url "):
        url = prompt.split(" ", 2)[2].strip()
        return ("open_url", {"url": url[:2048]})

    # Tap coordinates: "tap 500 600"
    m = re.match(r".*tap\s+(\d{2,4})\s+(\d{2,4}).*", p)
    if m:
        return ("tap", {"x": int(m.group(1)), "y": int(m.group(2))})

    # Swipe: "swipe 500 1600 500 600"
    m = re.match(r".*swipe\s+(\d{2,4})\s+(\d{2,4})\s+(\d{2,4})\s+(\d{2,4}).*", p)
    if m:
        return ("swipe", {"x1": int(m.group(1)), "y1": int(m.group(2)), "x2": int(m.group(3)), "y2": int(m.group(4))})

    # Type text: "type hello world"
    if p.startswith("type "):
        text = prompt.split(" ", 1)[1]
        return ("type_text", {"text": text[:200]})

    # Navigation: home/back/recents/notifications
    if "go home" in p or p.strip() == "home":
        return ("nav_home", {})
    if "back" in p:
        return ("nav_back", {})
    if "recents" in p:
        return ("nav_recents", {})
    if "notifications" in p:
        return ("open_notifications", {})

    # Wifi on/off
    if "wifi on" in p or "enable wifi" in p:
        return ("wifi", {"enabled": True})
    if "wifi off" in p or "disable wifi" in p:
        return ("wifi", {"enabled": False})
    return DEFAULT_TASK
