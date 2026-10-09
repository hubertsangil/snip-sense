"""Intelligent auto-naming and filename sanitization engine."""

import re
import sys
import time
from typing import Optional
from snipsense.core.models import OCRTextBox

STOP_WORDS = {
    "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "is", "it", "this", "that", "from", "by", "as", "be", "are", "was", "were",
    "you", "your", "my", "our", "all", "not", "but", "so", "if", "then"
}

KNOWN_APP_MAPPINGS = {
    "visual studio code": "VSCode",
    "code": "VSCode",
    "google chrome": "Chrome",
    "chrome": "Chrome",
    "mozilla firefox": "Firefox",
    "firefox": "Firefox",
    "microsoft edge": "Edge",
    "edge": "Edge",
    "discord": "Discord",
    "slack": "Slack",
    "terminal": "Terminal",
    "powershell": "PowerShell",
    "cmd": "CommandPrompt",
    "command prompt": "CommandPrompt",
    "spotify": "Spotify",
    "figma": "Figma",
    "notepad": "Notepad",
    "steam": "Steam",
}


def get_foreground_window_title() -> str:
    """Queries the OS active foreground window title in sub-5ms."""
    if sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if hwnd:
                buf = ctypes.create_unicode_buffer(512)
                length = user32.GetWindowTextW(hwnd, buf, 512)
                if length > 0:
                    return buf.value.strip()
        except Exception:
            pass
    elif sys.platform == "darwin":
        try:
            import subprocess
            cmd = 'tell application "System Events" to get name of first application process whose frontmost is true'
            output = subprocess.check_output(["osascript", "-e", cmd], timeout=0.1)
            return output.decode("utf-8", errors="ignore").strip()
        except Exception:
            pass
    return ""


def extract_app_name(window_title: str) -> str:
    """Extracts a concise, standardized application slug from a window title."""
    if not window_title or not window_title.strip():
        return ""

    title = window_title.strip()
    title_lower = title.lower()

    # 1. Match known application names anywhere in title
    for needle, clean_name in KNOWN_APP_MAPPINGS.items():
        # Match as discrete word or boundary
        if re.search(r'\b' + re.escape(needle) + r'\b', title_lower):
            return clean_name

    # 2. Extract standard Windows title tail: "Document - AppName" or "Document — AppName"
    delimiters = [" - ", " — ", " | "]
    for delim in delimiters:
        if delim in title:
            parts = title.split(delim)
            tail = parts[-1].strip()
            # Clean tail
            cleaned = re.sub(r'[^a-zA-Z0-9]', '', tail)
            if 2 <= len(cleaned) <= 18:
                return cleaned

    # 3. Fallback: Take first clean word
    words = re.findall(r'[A-Za-z0-9]+', title)
    if words:
        candidate = words[0].capitalize()
        if 2 <= len(candidate) <= 16:
            return candidate

    return ""


def extract_dominant_keyword(ocr_boxes: list[OCRTextBox]) -> str:
    """Extracts high-prominence headline keywords from OCR text blocks, filtering stop words."""
    if not ocr_boxes:
        return ""

    # Sort boxes by size (width * height) and confidence descending
    sorted_boxes = sorted(
        ocr_boxes,
        key=lambda b: (b.width * b.height * (b.confidence if b.confidence > 0 else 0.5)),
        reverse=True
    )

    meaningful_words: list[str] = []
    for box in sorted_boxes[:4]:
        # Extract alphanumeric words
        tokens = re.findall(r'[A-Za-z0-9]{3,}', box.text)
        for token in tokens:
            if token.lower() not in STOP_WORDS and len(token) >= 3:
                # Capitalize
                clean_word = token.capitalize()
                if clean_word not in meaningful_words:
                    meaningful_words.append(clean_word)
                    if len(meaningful_words) >= 2:
                        break
        if len(meaningful_words) >= 2:
            break

    return "_".join(meaningful_words)


def sanitize_filename(name: str) -> str:
    """Sanitizes a candidate filename to ensure strict filesystem safety."""
    # Strip illegal Windows/POSIX characters
    clean = re.sub(r'[\\/*?:"<>|]', '', name)
    # Replace spaces and punctuation with underscores
    clean = re.sub(r'[\s\-]+', '_', clean)
    # Remove duplicate underscores
    clean = re.sub(r'_+', '_', clean)
    # Trim leading/trailing underscores and dots
    clean = clean.strip('_.')
    # Limit length
    if len(clean) > 50:
        clean = clean[:50].rstrip('_')
    return clean or "Snip"


def generate_filename(
    window_title: str = "",
    ocr_boxes: list[OCRTextBox] | None = None,
    timestamp: Optional[float] = None,
) -> str:
    """Synthesizes an intelligent, human-readable filename for a capture."""
    t = timestamp or time.time()
    time_str = time.strftime("%Y%m%d_%H%M%S", time.localtime(t))

    app_name = sanitize_filename(extract_app_name(window_title))
    ocr_keyword = sanitize_filename(extract_dominant_keyword(ocr_boxes or []))

    if app_name and ocr_keyword:
        base = f"{app_name}_{ocr_keyword}_{time_str}"
    elif app_name:
        base = f"{app_name}_Capture_{time_str}"
    elif ocr_keyword:
        base = f"Capture_{ocr_keyword}_{time_str}"
    else:
        base = f"Snip_{time_str}"

    sanitized = sanitize_filename(base)
    return f"{sanitized}.png"
