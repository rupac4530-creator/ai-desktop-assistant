# vision/template_match.py
"""Template matching for finding UI elements by image."""

import os
from PIL import Image

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

from .screen_capture import capture_fullscreen

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'templates')


def ensure_templates_dir():
    """Ensure templates directory exists."""
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    return TEMPLATES_DIR


def find_template_on_screen(template_path, threshold=0.8, grayscale=True):
    """
    Find a template image on the current screen.
    
    Args:
        template_path: Path to template image file
        threshold: Match confidence threshold (0.0-1.0)
        grayscale: Whether to convert to grayscale for matching
    
    Returns:
        Dict with 'x', 'y', 'w', 'h', 'score', 'center_x', 'center_y' if found,
        None if not found
    """
    if cv2 is None or np is None:
        raise ImportError("opencv-python not installed. Run: pip install opencv-python-headless")
    
    if not os.path.exists(template_path):
        print(f"[TemplateMatch] Template not found: {template_path}")
        return None
    
    # Capture screen
    screen_img = capture_fullscreen()
    screen = np.array(screen_img)
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
    
    # Load template
    template = cv2.imread(template_path)
    if template is None:
        print(f"[TemplateMatch] Failed to load template: {template_path}")
        return None
    
    # Convert to grayscale if requested
    if grayscale:
        screen = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    
    # Template matching
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    if max_val >= threshold:
        th, tw = template.shape[:2]
        tx, ty = max_loc
        return {
            "x": tx,
            "y": ty,
            "w": tw,
            "h": th,
            "score": float(max_val),
            "center_x": tx + tw // 2,
            "center_y": ty + th // 2
        }
    
    return None


def find_all_templates(template_path, threshold=0.8, max_results=10, grayscale=True):
    """
    Find all occurrences of a template image on screen.
    
    Args:
        template_path: Path to template image file
        threshold: Match confidence threshold (0.0-1.0)
        max_results: Maximum number of matches to return
        grayscale: Whether to convert to grayscale for matching
    
    Returns:
        List of match dicts sorted by score (highest first)
    """
    if cv2 is None or np is None:
        raise ImportError("opencv-python not installed")
    
    if not os.path.exists(template_path):
        return []
    
    # Capture screen
    screen_img = capture_fullscreen()
    screen = np.array(screen_img)
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
    
    # Load template
    template = cv2.imread(template_path)
    if template is None:
        return []
    
    th, tw = template.shape[:2]
    
    # Convert to grayscale if requested
    if grayscale:
        screen = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    
    # Template matching
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    
    # Find all locations above threshold
    locations = np.where(result >= threshold)
    matches = []
    
    for pt in zip(*locations[::-1]):
        tx, ty = pt
        score = result[ty, tx]
        
        # Check for overlap with existing matches (avoid duplicates)
        is_duplicate = False
        for existing in matches:
            if abs(existing['x'] - tx) < tw // 2 and abs(existing['y'] - ty) < th // 2:
                is_duplicate = True
                break
        
        if not is_duplicate:
            matches.append({
                "x": int(tx),
                "y": int(ty),
                "w": tw,
                "h": th,
                "score": float(score),
                "center_x": tx + tw // 2,
                "center_y": ty + th // 2
            })
    
    # Sort by score and limit results
    matches.sort(key=lambda m: m['score'], reverse=True)
    return matches[:max_results]


def save_template_from_region(x, y, w, h, name):
    """
    Save a screen region as a template for future matching.
    
    Args:
        x, y: Top-left corner coordinates
        w, h: Width and height
        name: Template name (will be saved as {name}.png)
    
    Returns:
        Path to saved template
    """
    from .screen_capture import capture_region
    
    ensure_templates_dir()
    img = capture_region(x, y, w, h)
    
    save_path = os.path.join(TEMPLATES_DIR, f"{name}.png")
    img.save(save_path, 'PNG')
    
    print(f"[TemplateMatch] Saved template: {save_path}")
    return save_path


def click_template(template_path, threshold=0.8):
    """
    Find template on screen and click its center.
    
    Args:
        template_path: Path to template image
        threshold: Match confidence threshold
    
    Returns:
        True if found and clicked, False otherwise
    """
    try:
        import pyautogui
    except ImportError:
        print("[TemplateMatch] pyautogui not installed for clicking")
        return False
    
    match = find_template_on_screen(template_path, threshold)
    if match:
        pyautogui.click(match['center_x'], match['center_y'])
        print(f"[TemplateMatch] Clicked at ({match['center_x']}, {match['center_y']})")
        return True
    
    print("[TemplateMatch] Template not found on screen")
    return False
