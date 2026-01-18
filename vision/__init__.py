# vision module - screen capture, OCR, template matching
from .screen_capture import capture_fullscreen, capture_region
from .ocr import image_to_text, extract_text_from_screen
from .template_match import find_template_on_screen, find_all_templates

__all__ = [
    'capture_fullscreen',
    'capture_region', 
    'image_to_text',
    'extract_text_from_screen',
    'find_template_on_screen',
    'find_all_templates'
]
