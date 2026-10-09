# 03: One-Click Privacy Shield (Auto-Blur & Granular Masking)

**What to build:** The preview toolbar features a prominent "Shield PII" button. When clicked, the engine automatically analyzes all detected OCR text blocks against a comprehensive suite of privacy patterns (emails, API tokens, passwords, private keys, IPv4/MAC addresses, credit card candidates). Matching regions have a pixel-level Gaussian blur or frosted mask permanently applied to their corresponding image coordinates. The user can also manually click on any individual text bounding box to toggle its blur state on or off. Copying or saving the image produces the masked result.

**Blocked by:** 02: In-Process OCR & Interactive Text Bounding Boxes

**Status:** completed

- [x] "Shield PII" action button is clearly visible and accessible on the capture preview toolbar.
- [x] Pattern detector accurately recognizes:
  - Email addresses
  - API keys and tokens (e.g., `sk_live_...`, `ghp_...`, Bearer tokens, AWS secrets)
  - IP addresses and network identifiers
  - Passwords and credential pairs (e.g., `password: ...`, `secret=...`)
  - Credit card candidate numbers
- [x] Clicking "Shield PII" applies Gaussian blur directly to the pixel data underlying all sensitive bounding boxes in memory.
- [x] Clicking any individual bounding box manually toggles its masked/unmasked state, allowing users to redact non-pattern text or unmask false positives.
- [x] When masked, copying the image (`Ctrl+C` or "Copy Image") or saving writes the redacted pixel buffer, guaranteeing zero sensitive text leakage.
- [x] Redacted text is omitted or replaced with `[REDACTED]` when the user triggers "Copy All Text".
