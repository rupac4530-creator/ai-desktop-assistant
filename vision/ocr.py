# vision/ocr.py
"""OCR wrapper using pytesseract for text extraction from images."""

import os
import shutil
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

from .screen_capture import capture_fullscreen, capture_region

# Auto-detect Tesseract installation
_tesseract_available = False
TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]

if pytesseract:
    if shutil.which("tesseract"):
        _tesseract_available = True
    else:
        for path in TESSERACT_PATHS:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                _tesseract_available = True
                break


def is_available() -> bool:
    """Check if Tesseract OCR is available."""
    return _tesseract_available and pytesseract is not None


def preprocess_image(pil_image, enhance=True):
    """
    Preprocess image for better OCR accuracy.
    
    Args:
        pil_image: PIL Image object
        enhance: Whether to apply enhancement (grayscale, threshold)
    
    Returns:
        Preprocessed PIL Image
    """
    if not enhance or cv2 is None or np is None:
        return pil_image
    
    # Convert to numpy array
    img_array = np.array(pil_image)
    
    # Convert to grayscale
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Apply adaptive thresholding for better text contrast
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)
    
    return Image.fromarray(denoised)


def image_to_text(pil_image, lang='eng', enhance=True):
    """
    Extract text from a PIL Image using OCR.
    
    Args:
        pil_image: PIL Image object
        lang: Tesseract language code (e.g., 'eng', 'hin', 'eng+hin')
        enhance: Whether to preprocess image for better accuracy
    
    Returns:
        Extracted text as string
    """
    if pytesseract is None:
        raise ImportError("pytesseract not installed. Run: pip install pytesseract")
    
    # Preprocess for better OCR
    processed = preprocess_image(pil_image, enhance)
    
    try:
        text = pytesseract.image_to_string(processed, lang=lang)
        return text.strip()
    except Exception as e:
        print(f"[OCR] Error: {e}")
        # Try without preprocessing as fallback
        try:
            text = pytesseract.image_to_string(pil_image, lang=lang)
            return text.strip()
        except Exception as e2:
            print(f"[OCR] Fallback also failed: {e2}")
            return ""


def extract_text_from_screen(lang='eng'):
    """
    Capture the screen and extract all visible text.
    
    Args:
        lang: Tesseract language code
    
    Returns:
        Extracted text as string
    """
    img = capture_fullscreen()
    return image_to_text(img, lang=lang)


def extract_text_from_region(x, y, w, h, lang='eng'):
    """
    Capture a screen region and extract text from it.
    
    Args:
        x, y: Top-left corner coordinates
        w, h: Width and height of region
        lang: Tesseract language code
    
    Returns:
        Extracted text as string
    """
    img = capture_region(x, y, w, h)
    return image_to_text(img, lang=lang)


def get_text_with_positions(pil_image, lang='eng'):
    """
    Extract text with bounding box positions.
    
    Args:
        pil_image: PIL Image object
        lang: Tesseract language code
    
    Returns:
        List of dicts with 'text', 'x', 'y', 'w', 'h', 'conf' keys
    """
    if pytesseract is None:
        raise ImportError("pytesseract not installed")
    
    try:
        data = pytesseract.image_to_data(pil_image, lang=lang, output_type=pytesseract.Output.DICT)
        
        results = []
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            text = data['text'][i].strip()
            conf = int(data['conf'][i])
            if text and conf > 30:  # Filter low-confidence and empty
                results.append({
                    'text': text,
                    'x': data['left'][i],
                    'y': data['top'][i],
                    'w': data['width'][i],
                    'h': data['height'][i],
                    'conf': conf
                })
        return results
    except Exception as e:
        print(f"[OCR] Error getting positions: {e}")
        return []


def find_text_on_screen(search_text, lang='eng'):
    """
    Find specific text on screen and return its position.
    
    Args:
        search_text: Text to find (case-insensitive substring match)
        lang: Tesseract language code
    
    Returns:
        List of matching positions with bounding boxes, or empty list if not found
    """
    img = capture_fullscreen()
    all_text = get_text_with_positions(img, lang)
    
    search_lower = search_text.lower()
    matches = [
        item for item in all_text
        if search_lower in item['text'].lower()
    ]
    
    return matches
