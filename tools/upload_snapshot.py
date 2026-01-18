# tools/upload_snapshot.py
"""
Upload latest snapshot to off-site URL.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

SNAPSHOTS_DIR = Path(__file__).parent.parent / "logs" / "snapshots"
UPLOAD_URL = os.getenv("SELF_UPDATE_UPLOAD_URL", "")
UPLOAD_TOKEN = os.getenv("SELF_UPDATE_UPLOAD_TOKEN", "")


def get_latest_snapshot() -> Path:
    """Find the most recent snapshot zip."""
    if not SNAPSHOTS_DIR.exists():
        return None
    
    zips = sorted(
        [p for p in SNAPSHOTS_DIR.iterdir() if p.suffix == ".zip"],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    return zips[0] if zips else None


def upload_snapshot(path: Path) -> bool:
    """Upload snapshot to configured URL."""
    if not UPLOAD_URL:
        print("No SELF_UPDATE_UPLOAD_URL configured")
        return False
    
    try:
        import requests
        
        headers = {}
        if UPLOAD_TOKEN:
            headers["Authorization"] = f"Bearer {UPLOAD_TOKEN}"
        
        print(f"Uploading {path.name} to {UPLOAD_URL}...")
        
        with open(path, "rb") as f:
            files = {"file": (path.name, f, "application/zip")}
            resp = requests.post(UPLOAD_URL, files=files, headers=headers, timeout=300)
        
        if resp.status_code in (200, 201):
            print(f" Upload successful: {resp.status_code}")
            return True
        else:
            print(f" Upload failed: {resp.status_code} - {resp.text[:200]}")
            return False
    
    except Exception as e:
        print(f" Upload error: {e}")
        return False


def main():
    snapshot = get_latest_snapshot()
    
    if not snapshot:
        print("No snapshots found")
        return 1
    
    print(f"Latest snapshot: {snapshot}")
    print(f"Size: {snapshot.stat().st_size / 1024 / 1024:.2f} MB")
    
    if upload_snapshot(snapshot):
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())
