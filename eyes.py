import mss
from PIL import Image

# The screenshot taken the instant ALT+K is pressed (before terminal gets focus)
_pre_capture = None


def snapshot():
    """
    Called the INSTANT the user presses ALT+K.
    Captures whatever is on screen at that exact moment —
    browser, editor, game, anything — before the terminal steals focus.
    """
    global _pre_capture
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]   # full primary monitor
            raw = sct.grab(monitor)
            img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
            img.thumbnail((1280, 720))  # shrink for fast upload
            _pre_capture = img
        print("[Eyes] Screen snapshot taken.")
        return _pre_capture
    except Exception as e:
        print(f"[Eyes] Snapshot failed: {e}")
        return None


def get_snapshot():
    """Return the last pre-captured snapshot."""
    return _pre_capture


def capture_screen():
    """Legacy alias — same as snapshot()."""
    return snapshot()


def get_latest_view():
    """Legacy alias — same as get_snapshot()."""
    return _pre_capture