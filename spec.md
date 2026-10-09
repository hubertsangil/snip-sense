# Spec: SnipSense — Offline-First AI-Native Screenshot & Capture Studio

## Problem Statement

Every day, computer users take dozens of screenshots (`Win+Shift+S`, `PrintScreen`) of error messages, chat snippets, financial confirmations, research slides, and recipes. However, the current default tools create four critical points of friction:

1. **Accidental Privacy & Security Leaks:** Screenshots routinely capture sensitive information—such as emails, API keys, passwords, home addresses, and credit card numbers. Redacting this information manually using traditional markup tools takes considerable effort, leading users to accidentally leak confidential credentials and personal data when sharing clips on Slack, GitHub, or Discord.
2. **Digital File Landfills & Useless Naming:** Operating systems save captures as generic filenames (e.g., `Screenshot 2026-10-09 18.31.png`), quickly turning desktop and pictures directories into unmanageable clutter.
3. **Unsearchable Visual Graveyards:** Operating systems only index filenames, not the text inside images. When users need to retrieve a Wi-Fi password, confirmation code, or error message captured two weeks prior, it is practically impossible to find without opening hundreds of image files one by one.
4. **Cloud Privacy Violation:** Commercial AI-assisted capture utilities require uploading images to remote cloud servers, which violates enterprise compliance, exposes personal data, and introduces unacceptable latency into a workflow that requires sub-second speed.

## Solution

**SnipSense** is an open-source, zero-prerequisite, 100% offline desktop capture studio and overlay HUD built with Python and PyQt6. It acts as an intelligent replacement for default snipping utilities:

- **One-Click Privacy Shield:** Uses embedded, in-process OCR (`RapidOCR` ONNX) and local pattern matchers to detect sensitive entities (emails, tokens, passwords, credit cards) and apply pixel-level Gaussian blur or mask them with a single click before sharing. Users can also click individual bounding boxes to toggle blurring interactively.
- **Hybrid Auto-Naming & Semantic Grouping:** Combines active foreground window metadata with dominant OCR headlines and a fallback-resilient micro-SLM to automatically save captures with human-readable titles (e.g., `VSCode_Docker_Exit137.png`) and smart tags.
- **Instant Visual Memory Search:** Automatically detects and indexes both new and historical screenshots (from `Pictures/Screenshots`) into an embedded SQLite FTS5 database, allowing users to query past captures in plain text (`Alt + F`) with sub-50ms latency.
- **Gaming-Style Overlay HUD (`Alt + Z`):** A translucent, frosted-glass overlay providing a carousel of recent captures, one-click PII badges, duplicate cleanup via perceptual hashing (`imagehash`), and a 30-second silent GIF/MP4 recorder for rapid bug and UI sharing.
- **Zero External Prerequisites:** Runs entirely self-contained without requiring external servers, daemons, or tools like Ollama or system Tesseract binaries.

---

## User Stories

1. As a developer, I want to take a screenshot of a terminal crash with `Win+Shift+S`, so that I can capture the relevant error without leaving my workspace.
2. As a software engineer, I want the mini-toolbar to appear right next to my cursor upon completing a crop, so that I can take immediate action without context-switching.
3. As a developer sharing a bug in public Slack, I want a one-click "Shield PII" button, so that my hardcoded API keys and internal IP addresses are automatically blurred before sharing.
4. As a user reviewing an auto-blurred capture, I want to click any individual detected text box to toggle its blur state, so that I maintain granular control over what gets masked.
5. As a privacy-conscious user, I want all OCR and entity detection to run locally in-process, so that sensitive bank or health details are never transmitted over the internet.
6. As a student capturing study slides, I want a "Copy Text" button on the mini-toolbar, so that I can copy lecture notes directly out of the image without retyping them.
7. As a busy worker, I want screenshots to automatically save with meaningful names like `Chrome_Amazon_OrderReceipt.png`, so that I never have to manually rename `Screenshot (84).png`.
8. As a user operating on battery or lower-spec machines, I want hybrid auto-naming to prioritize foreground window metadata and OCR headers in under 5ms, so that the tool never lags my system.
9. As a gamer or creator in full-screen applications, I want to press `Alt+Z` to summon a translucent frosted-glass HUD overlay, so that I can manage my recent captures without minimizing my active game or application.
10. As a user with multiple repeated captures of the same bug, I want the system to detect perceptual duplicates using `imagehash`, so that I can clean up redundant screenshots with a single click.
11. As a new user opening SnipSense for the first time, I want it to automatically locate and index my existing `Pictures/Screenshots` directory in the background, so that my historical captures become instantly searchable without manual import steps.
12. As a user looking for a flight confirmation code taken last month, I want to press `Alt+F` and type "flight confirmation", so that the exact screenshot is retrieved in under 50ms.
13. As a QA tester, I want to trigger a short screen recording (up to 30s) directly from the overlay HUD, so that I can quickly demonstrate a UI glitch.
14. As a remote teammate, I want my recorded clip to export as an optimized, silent animated GIF or MP4, so that it can be dropped directly into GitHub issues or Slack messages.
15. As a hackathon participant or general user, I want to launch the application without installing Ollama or configuring environment PATH variables, so that I can get started immediately without setup friction.
16. As a user who took a screenshot of confidential medical lab results, I want the option to copy the image directly to the clipboard with PII masked without saving it permanently to disk.
17. As a power user, I want to customize the default hotkeys in settings, so that SnipSense does not conflict with existing shortcuts in my IDE or games.
18. As a user searching through visual memory, I want search query matches highlighted directly on the image preview, so that I can immediately spot the relevant information.
19. As a user who values privacy, I want to view a persistent "100% Offline | Zero Cloud Egress" badge on the HUD, so that I can verify that no network sockets are open.
20. As a user with limited disk space, I want an overview badge in the HUD showing the total space saved by cleaning duplicate screenshots.

---

## Implementation Decisions

### 1. Unified Monolithic Python Architecture
- Built entirely in Python 3.10+ using PyQt6 for all visual components.
- Avoids multi-process IPC and electron/sidecar friction, allowing the UI and data processing to share in-memory image buffers directly.

### 2. High-Performance Screen Capture Pipeline
- Screen capture executed via `mss` for sub-10ms full-screen and region grabbing.
- The snipping canvas implemented as a frameless, transparent full-screen overlay widget (`Qt.WindowType.FramelessWindowHint` and `Qt.WindowType.WindowStaysOnTopHint`) that captures bounding coordinates upon mouse release.

### 3. In-Process OCR & Sensitive Entity Detection
- In-process OCR powered by `rapidocr-onnxruntime`, eliminating any external installation of Tesseract binaries.
- OCR outputs character bounding polygons and normalized bounding boxes `(x, y, w, h)` along with recognition confidence scores.
- Sensitive entity recognition implemented as a modular rule and pattern evaluation engine targeting:
  - Email addresses (`[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+`)
  - API Keys and Secrets (patterns for `sk_`, `ghp_`, `bearer`, JWT tokens, AWS access keys)
  - Financial data (credit card Luhn pattern candidates, IBAN, bank account numbers)
  - Network and system identifiers (IPv4, IPv6, MAC addresses)
- Masking applied via `cv2.GaussianBlur` or PIL pixelation directly onto the selected bounding box pixel regions in memory.

### 4. Hybrid Intelligent Naming Engine
- Step 1 (Heuristic Fast Path): Queries the Win32 active window title via `ctypes.windll.user32.GetForegroundWindow` / `GetWindowTextW` and extracts the top high-confidence headline from the OCR token hierarchy in under 5ms.
- Step 2 (Optional In-Process Micro-SLM): Uses `llama-cpp-python` with an optional bundled quantized model (`Qwen2.5-0.5B-Instruct-Q4_K_M.gguf`, ~390MB) for complex semantic summarization. If the model file is not present, the engine automatically falls back to the fast heuristic name without warning or failure.

### 5. Persistent Storage & Visual Memory Search
- Local metadata and full-text index managed via embedded `sqlite3` utilizing the FTS5 virtual table extension.
- Schema captures:
  - `id` (INTEGER PRIMARY KEY)
  - `file_path` (TEXT UNIQUE)
  - `created_at` (DATETIME)
  - `title` (TEXT)
  - `ocr_text` (TEXT)
  - `tags` (TEXT)
  - `perceptual_hash` (TEXT)
  - `is_duplicate_of` (INTEGER NULLABLE)
- FTS5 virtual table indexes `title`, `ocr_text`, and `tags` for sub-millisecond lexical search queries.

### 6. Perceptual Deduplication
- Utilizes `imagehash` (difference hash `dhash` and average hash `ahash`).
- Files with a Hamming distance $\le 4$ are tagged as duplicate candidates, grouped under the earliest chronological capture, and presented in the HUD with a 1-click batch cleanup option.

### 7. Overlay HUD & Floating Mini-Toolbar
- Mini-toolbar implemented as a floating, frameless PyQt6 widget with rounded corners and dark-mode styling, anchored dynamically to the lower-right corner of the user's selected crop region.
- Full HUD implemented as an `Alt+Z` modal dialog featuring a semi-transparent dark backdrop, an active carousel of recent items, a search input bar, and quick action trigger buttons.

### 8. Screen Recording Pipeline
- Lightweight screen recording implemented using an `mss` frame-capture loop running in a dedicated `QThread`.
- Frames encoded to animated GIF or H.264 MP4 using `imageio` and `imageio-ffmpeg` (which bundles static, portable ffmpeg binaries within the Python wheel, requiring zero manual installation).

---

## Testing Decisions

### Core Testing Philosophy
- Tests must verify observable, end-to-end behavior at the highest possible architectural seam rather than internal implementation details.
- GUI widgets and native screen hardware drivers must be decoupled from business logic so test suites can run completely headless in automated CI environments.

### Proposed Primary Testing Seam: `SnipSenseCore` Facade
The primary testing seam is the unified controller facade: **`SnipSenseCore`**. It exposes high-level, headless methods accepting image buffers or file paths:
1. `process_capture(image_bytes, window_title) -> CaptureResult`
   - Verifies: OCR extraction, PII entity detection, generated title, assigned tags, and calculated perceptual hash.
2. `apply_privacy_shield(capture_id, mask_all_pii=True, toggle_boxes=[]) -> ProcessedImageBytes`
   - Verifies: Pixel transformation applied to sensitive bounding boxes while leaving non-sensitive areas intact.
3. `search_vault(query_text) -> List[SearchResult]`
   - Verifies: FTS5 database retrieval accuracy, ranking, and speed.
4. `scan_and_index_directory(folder_path) -> IndexSummary`
   - Verifies: Correct batch ingestion of existing images and duplicate detection clustering.
5. `export_recording(frame_buffer, format="gif") -> Path`
   - Verifies: Generation of valid GIF/MP4 files with non-zero byte size.

### Prior Art
- Standard Python test suite utilizing `pytest`. Synthetic test images with embedded email addresses, API tokens, and known layouts will be placed in a `tests/fixtures/` directory to ensure deterministic test execution.

---

## Out of Scope

- Multi-track microphone and system audio mixing during video recordings (silent recordings only for the MVP to prevent driver sync issues).
- Cloud sync, user accounts, and remote backup storage.
- Full desktop screenshot editor with vector drawing tools (pen, highlighter, arrows)—focus is strictly on automated capture, privacy shielding, naming, and retrieval.
- OCR language packs beyond English and common Latin scripts for the initial hackathon release.

---

## Further Notes

- All dependencies are pure Python wheels or pre-compiled binaries bundled in the package (`rapidocr-onnxruntime`, `imageio-ffmpeg`, `PyQt6`).
- Future enhancements post-hackathon include system tray minimization, custom keyboard shortcuts configuration UI, and optional export plugins to Obsidian and Notion local markdown vaults.
