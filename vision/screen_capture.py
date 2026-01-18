# vision/screen_capture.py
"""Fast cross-platform screen capture using mss."""

import os
import time
from PIL import Image

try:
    import mss
    import mss.tools
except ImportError:
    mss = None

SNAPSHOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'snapshots')


def ensure_snapshots_dir():
    """Ensure snapshots directory exists."""
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    return SNAPSHOTS_DIR


def capture_fullscreen(save_path=None, monitor_index=1):
    """
    Capture the full screen (primary monitor by default).
    
    Args:
        save_path: Optional path to save PNG. If None, generates timestamped path.
        monitor_index: Which monitor to capture (1 = primary, 0 = all monitors combined)
    
    Returns:
        PIL.Image object of the captured screen
    """
    if mss is None:
        raise ImportError("mss not installed. Run: pip install mss")
    
    with mss.mss() as sct:
        monitor = sct.monitors[monitor_index]
        sct_img = sct.grab(monitor)
        
        # Convert to PIL Image
        img = Image.frombytes('RGB', sct_img.size, sct_img.bgra, 'raw', 'BGRX')
        
        if save_path:
            ensure_snapshots_dir()
            img.save(save_path, 'PNG')
        
        return img


def capture_region(x, y, w, h, save_path=None):
    """
    Capture a specific region of the screen.
    
    Args:
        x, y: Top-left corner coordinates
        w, h: Width and height of region
        save_path: Optional path to save PNG
    
    Returns:
        PIL.Image object of the captured region
    """
    if mss is None:
        raise ImportError("mss not installed. Run: pip install mss")
    
    with mss.mss() as sct:
        region = {"left": x, "top": y, "width": w, "height": h}
        sct_img = sct.grab(region)
        
        # Convert to PIL Image
        img = Image.frombytes('RGB', sct_img.size, sct_img.bgra, 'raw', 'BGRX')
        
        if save_path:
            ensure_snapshots_dir()
            img.save(save_path, 'PNG')
        
        return img


def capture_with_timestamp(prefix="screen"):
    """
    Capture fullscreen with automatic timestamped filename.
    
    Returns:
        tuple: (PIL.Image, save_path)
    """
    ensure_snapshots_dir()
    timestamp = int(time.time() * 1000)
    save_path = os.path.join(SNAPSHOTS_DIR, f"{prefix}_{timestamp}.png")
    img = capture_fullscreen(save_path)
    return img, save_path


def list_monitors():
    """List all available monitors with their dimensions."""
    if mss is None:
        return []
    
    with mss.mss() as sct:
        return [
            {
                "index": i,
                "left": m["left"],
                "top": m["top"],
                "width": m["width"],
                "height": m["height"]
            }
            for i, m in enumerate(sct.monitors)
        ]
