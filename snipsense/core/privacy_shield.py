"""Pattern-based PII detector and privacy shielding engine."""

import re
from typing import NamedTuple, Pattern
from PIL import Image
from snipsense.core.models import OCRTextBox


class DetectedPII(NamedTuple):
    """Represents a sensitive text match within a text box."""
    category: str
    matched_text: str
    box: OCRTextBox


# Regex patterns covering Issue #3 requirements
# 1. Email addresses
EMAIL_REGEX = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
)

# 2. API Keys and Tokens (ghp_, sk_live_, gho_, bearer, AWS keys, generic hex/base64 tokens)
# - GitHub tokens: ghp_, gho_, ghu_, ghs_, ghr_ followed by alphanumeric chars
# - Stripe secret/live keys: sk_live_[0-9a-zA-Z]{24,}, rk_live_..., sk_test_...
# - AWS Access Key ID: AKIA[0-9A-Z]{16}
# - Bearer tokens: Bearer\s+[A-Za-z0-9\-_.~+/=]{16,}
# - Generic API key keywords: (?:api[_-]?key|secret|token)[\s:=]+['"]?[A-Za-z0-9_\-]{16,}['"]?
API_KEY_REGEXES = [
    re.compile(r'\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b'),
    re.compile(r'\b(?:sk|rk)_(?:live|test)_[0-9a-zA-Z]{16,}\b'),
    re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
    re.compile(r'(?i)\bbearer\s+[A-Za-z0-9\-_.]{16,}\b'),
    re.compile(r'(?i)\b(?:api[_-]?key|token|access[_-]?token)[\s:=]+["\']?([A-Za-z0-9_\-]{16,})["\']?'),
]

# 3. Private Keys (e.g., -----BEGIN [A-Z ]*PRIVATE KEY-----)
PRIVATE_KEY_REGEX = re.compile(
    r'-----BEGIN\s+(?:[A-Z\s]+)?PRIVATE\s+KEY-----',
    re.IGNORECASE
)

# 4. Passwords and credential pairs (e.g. password: ..., secret=...)
PASSWORD_PAIR_REGEX = re.compile(
    r'(?i)\b(?:password|passwd|pwd|secret|client[_-]?secret)[\s:=]+["\']?([^\s"\';]{3,})["\']?'
)

# 5. IPv4 addresses and MAC addresses
# IPv4 with 0-255 octets
IPV4_REGEX = re.compile(
    r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
)
# MAC address: 6 groups of 2 hex digits separated by colon or hyphen
MAC_REGEX = re.compile(
    r'\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b'
)

# 6. Credit Card candidate numbers (13-19 digits, optionally spaced or hyphenated)
CREDIT_CARD_REGEX = re.compile(
    r'\b(?:\d{4}[-\s]?){3}\d{1,4}\b|\b\d{13,19}\b'
)


def luhn_checksum_valid(card_number: str) -> bool:
    """Validates candidate card number digits with Luhn algorithm."""
    digits = [int(c) for c in card_number if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    # Luhn check
    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = d * 2
            checksum += (doubled - 9) if doubled > 9 else doubled
        else:
            checksum += d
    return checksum % 10 == 0


class PrivacyShield:
    """Detects sensitive personal and credential information in text boxes."""

    @classmethod
    def is_sensitive_text(cls, text: str) -> tuple[bool, str]:
        """Evaluates whether the given text contains PII/secrets.
        
        Returns:
            Tuple of (is_sensitive: bool, category: str).
        """
        trimmed = text.strip()
        if not trimmed:
            return False, ""

        # Check Email
        if EMAIL_REGEX.search(trimmed):
            return True, "Email"

        # Check API Tokens
        for pattern in API_KEY_REGEXES:
            if pattern.search(trimmed):
                return True, "API Key / Token"

        # Check Private Keys
        if PRIVATE_KEY_REGEX.search(trimmed):
            return True, "Private Key"

        # Check Passwords / Credentials
        if PASSWORD_PAIR_REGEX.search(trimmed):
            return True, "Password / Secret"

        # Check IPv4 & MAC
        if IPV4_REGEX.search(trimmed):
            return True, "IP Address"
        if MAC_REGEX.search(trimmed):
            return True, "MAC Address"

        # Check Credit Card Candidates (with Luhn check if purely numerical formatted)
        for match in CREDIT_CARD_REGEX.finditer(trimmed):
            candidate = match.group(0)
            digits_only = re.sub(r'\D', '', candidate)
            if 13 <= len(digits_only) <= 19 and luhn_checksum_valid(digits_only):
                return True, "Credit Card"

        return False, ""

    @classmethod
    def detect_pii_boxes(cls, boxes: list[OCRTextBox]) -> list[OCRTextBox]:
        """Returns the subset of OCRTextBox instances that match sensitive PII patterns."""
        sensitive_boxes: list[OCRTextBox] = []
        for box in boxes:
            is_sens, _ = cls.is_sensitive_text(box.text)
            if is_sens:
                sensitive_boxes.append(box)
        return sensitive_boxes


def apply_blur_mask(
    image: "Image.Image",
    boxes: list[OCRTextBox],
    radius: float = 14.0,
) -> "Image.Image":
    """Applies a pixel-level Gaussian blur directly to regions defined by boxes.

    Args:
        image: Original PIL image.
        boxes: List of OCRTextBox bounding regions to mask.
        radius: Gaussian blur radius.

    Returns:
        A new PIL Image with the specified regions masked with Gaussian blur.
    """
    from PIL import ImageFilter

    if not boxes:
        return image.copy()

    result_img = image.copy()
    img_w, img_h = result_img.size

    for box in boxes:
        # Clamp bounding box coordinates to image dimensions
        left = max(0, min(box.x, img_w - 1))
        top = max(0, min(box.y, img_h - 1))
        right = max(left + 1, min(box.x + box.width, img_w))
        bottom = max(top + 1, min(box.y + box.height, img_h))

        crop_box = (left, top, right, bottom)
        cropped_region = result_img.crop(crop_box)
        blurred_region = cropped_region.filter(ImageFilter.GaussianBlur(radius=radius))
        result_img.paste(blurred_region, crop_box)

    return result_img

