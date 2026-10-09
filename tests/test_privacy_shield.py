"""Unit tests for the PrivacyShield pattern detection."""

from snipsense.core.models import OCRTextBox
from snipsense.core.privacy_shield import PrivacyShield, luhn_checksum_valid


def make_box(text: str) -> OCRTextBox:
    return OCRTextBox(
        text=text,
        confidence=0.99,
        x=10,
        y=10,
        width=100,
        height=20,
        polygon=[(10.0, 10.0), (110.0, 10.0), (110.0, 30.0), (10.0, 30.0)],
    )


def test_detect_emails():
    assert PrivacyShield.is_sensitive_text("user@example.com")[0] is True
    assert PrivacyShield.is_sensitive_text("Contact: admin.support+tag@sub.domain.org!")[0] is True
    assert PrivacyShield.is_sensitive_text("No email here hello world")[0] is False


def test_detect_api_tokens():
    # GitHub PAT
    assert PrivacyShield.is_sensitive_text("ghp_1234567890abcdefghijklmnopqrstuvwxyz")[0] is True
    # Stripe secret key
    assert PrivacyShield.is_sensitive_text("sk_live_51ABCDefgh1234567890uvwxyz")[0] is True
    assert PrivacyShield.is_sensitive_text("sk_test_51ABCDefgh1234567890uvwxyz")[0] is True
    # AWS access key
    assert PrivacyShield.is_sensitive_text("AKIAIOSFODNN7EXAMPLE")[0] is True
    # Bearer token
    assert PrivacyShield.is_sensitive_text("Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")[0] is True
    # API key pair
    assert PrivacyShield.is_sensitive_text("api_key: a1b2c3d4e5f6g7h8i9j0")[0] is True


def test_detect_private_keys():
    assert PrivacyShield.is_sensitive_text("-----BEGIN RSA PRIVATE KEY-----")[0] is True
    assert PrivacyShield.is_sensitive_text("-----BEGIN PRIVATE KEY-----")[0] is True


def test_detect_passwords_and_credentials():
    assert PrivacyShield.is_sensitive_text("password: superSecretPassword123!")[0] is True
    assert PrivacyShield.is_sensitive_text("client_secret = 'mySuperSecretKey99'")[0] is True
    assert PrivacyShield.is_sensitive_text("passwd: secretpass")[0] is True


def test_detect_ip_and_mac_addresses():
    assert PrivacyShield.is_sensitive_text("Server IP: 192.168.1.1 connected")[0] is True
    assert PrivacyShield.is_sensitive_text("10.0.0.254")[0] is True
    assert PrivacyShield.is_sensitive_text("Invalid 999.999.999.999")[0] is False
    assert PrivacyShield.is_sensitive_text("MAC: 00:1A:2B:3C:4D:5E")[0] is True
    assert PrivacyShield.is_sensitive_text("00-1A-2B-3C-4D-5E")[0] is True


def test_detect_credit_cards():
    # Valid Visa test card (passes Luhn)
    valid_visa = "4532 0150 0000 0007"
    assert luhn_checksum_valid(valid_visa) is True
    assert PrivacyShield.is_sensitive_text(f"Card: {valid_visa}")[0] is True

    # Invalid Luhn card number should not trigger credit card detection
    invalid_visa = "4532 0150 0000 0001"
    assert luhn_checksum_valid(invalid_visa) is False
    assert PrivacyShield.is_sensitive_text(f"Code: {invalid_visa}")[0] is False


def test_detect_pii_boxes():
    boxes = [
        make_box("Hello World"),
        make_box("john.doe@company.com"),
        make_box("Normal description text"),
        make_box("password: MyPassword123"),
    ]
    detected = PrivacyShield.detect_pii_boxes(boxes)
    assert len(detected) == 2
    assert detected[0].text == "john.doe@company.com"
    assert detected[1].text == "password: MyPassword123"


def test_apply_blur_mask():
    from PIL import Image
    from snipsense.core.privacy_shield import apply_blur_mask

    # Create image with high-contrast sharp details (simulating text characters)
    img = Image.new("RGB", (60, 60), color=(255, 255, 255))
    # Draw dark simulated text pixels inside region (10, 10, 40, 40)
    for y in range(15, 35, 2):
        for x in range(15, 35, 2):
            img.putpixel((x, y), (0, 0, 0))

    box = OCRTextBox(text="Secret", confidence=1.0, x=10, y=10, width=40, height=40, polygon=[])
    
    # Pre-blur check: pixel (15, 15) is pitch black (0, 0, 0)
    assert img.getpixel((15, 15)) == (0, 0, 0)

    blurred = apply_blur_mask(img, [box], radius=8.0)
    assert blurred.size == (60, 60)
    
    # Post-blur check: sharp black pixels are smoothed and blended into gray
    post_blur_pixel = blurred.getpixel((15, 15))
    assert post_blur_pixel != (0, 0, 0)
    assert post_blur_pixel != (255, 255, 255)


