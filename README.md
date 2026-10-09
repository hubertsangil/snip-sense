# SnipSense

### *The 100% Offline AI Desktop Capture Studio, Privacy Shield & Visual Memory HUD*

[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Local AI](https://img.shields.io/badge/AI%20Inference-100%25%20On--Device%20(Zero%20Cloud)-10B981?logo=cpu&logoColor=white)](#-theme-alignment-appbuildersph-2026)
[![Database](https://img.shields.io/badge/Visual%20Memory-SQLite%20FTS5-003B57?logo=sqlite&logoColor=white)](#-technologies-and-frameworks)
[![UI Framework](https://img.shields.io/badge/GUI-PyQt6-41CD52?logo=qt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Hackathon](https://img.shields.io/badge/AppBuildersPH-2026%20Hackathon-FF6B6B)](https://github.com/hubertsangil/snip-sense)

---

```
                                  [ BANNER IMAGE PLACEHOLDER ]
                         ╔═══════════════════════════════════════════╗
                         ║     S N I P S E N S E   S T U D I O       ║
                         ║   Local AI Screen Capture & Memory HUD    ║
                         ╚═══════════════════════════════════════════╝
```

---

## ⚡ Core Concept

**SnipSense** is an open-source, 100% offline desktop capture studio and frosted-glass overlay HUD that replaces legacy snipping tools with zero-cloud intelligence. Running embedded quantized ONNX OCR models and Shannon entropy heuristics directly on your hardware, SnipSense automatically masks sensitive credentials (API keys, tokens, PII), auto-generates semantic filenames from active window contexts, indexes screenshot text into a sub-50ms searchable SQLite FTS5 visual memory vault, and captures short GIF/MP4 repro clips without a single byte ever touching the cloud.

---

## 🎯 Why SnipSense? 

| # | Pain Point (The Status Quo) | SnipSense Solution (Local-First AI Architecture) |
|---|---|---|
| **1** | **Accidental Privacy & Security Leaks**<br>Developers and teams frequently leak live API tokens (`sk_live_...`, `ghp_...`), AWS credentials, passwords, and client PII when sharing debugging screenshots in Slack, Discord, or GitHub. | **Shield PII & Local Privacy Guard**<br>Scans OCR text on-the-fly using embedded heuristics, Luhn validation, and Shannon entropy analysis to detect high-entropy keys and sensitive patterns, instantly applying smooth Gaussian blurs with 1-click interactive toggles before sharing. |
| **2** | **Digital File Landfills & Useless Naming**<br>Default screenshot utilities dump unmanageable piles of filenames like `Screenshot 2026-10-09 18.31.png` across desktops, creating digital clutter that requires tedious manual renaming. | **Hybrid Semantic Auto-Naming**<br>Synthesizes foreground application metadata (e.g. `VSCode`, `Chrome`, `Terminal`) with dominant OCR keywords (e.g., `Postgres_Connection_Error`) to name captures instantly (e.g., `VSCode_Postgres_Connection_Error_20261010_0112.png`). |
| **3** | **Unsearchable Visual Graveyards**<br>Operating systems only index filenames, leaving the actual knowledge inside past screenshots lost and unsearchable. Finding a Wi-Fi code, error log, or receipt requires endless manual scrolling. | **Sub-50ms Visual Memory Vault (FTS5)**<br>Every capture is transactionally indexed into an embedded SQLite database backed by FTS5 full-text search. Pressing `Alt + F` summons a Spotlight-style search modal with real-time query matching, highlighted snippets, and instant text copying. |
| **4** | **Cloud Privacy Violations & Latency**<br>Cloud-based screenshot "AI assistants" upload private bitmaps and proprietary company IP to third-party servers, creating compliance risks, latency bottlenecks, and vendor lock-in. | **100% Offline, Zero Cloud Dependency**<br>All OCR inference, perceptual hashing, PII masking, full-text searching, and video clip encoding execute locally on device with sub-10ms response times. Zero API keys, zero subscriptions, zero network telemetry. |

---

## 🏆 Theme Alignment 

The **AppBuildersPH 2026 Hackathon** celebrates **"Local AI"**—useful, tangible AI experiences where meaningful computation happens strictly on the user's personal device rather than depending on cloud inference endpoints.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 LOCAL AI DATA FLOW                                     │
│                                                                                        │
│  [ Display Canvas ] ──► [ mss Sub-10ms Frame Grab ] ──► [ Quantized ONNX Inference ]   │
│                                                                   │                    │
│                                              ┌────────────────────┴────────────────┐   │
│                                              ▼                                     ▼   │
│                                   [ DBNet Text Detection ]            [ PII Shield & ] │
│                                   [ CRNN Recognition     ]            [ Entropy Engine]│
│                                              │                                     │   │
│                                              ▼                                     │   │
│  [ SQLite FTS5 Vault ] ◄── [ Semantic Auto-Naming ] ◄──────────────────────────────┘   │
│                                                                                        │
│  🔒 100% Local Hardware Loop • Zero Network Transmission • Zero External API Calls     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

SnipSense exemplifies this vision:
1. **Zero External API Dependencies**: Does not require OpenAI, Anthropic, or external cloud vision endpoints. Sensitive screens never leave RAM/disk.
2. **Local Quantized Neural Networks**: Runs optimized ONNX-runtime weights directly on local CPU/iGPU architectures for sub-second recognition.
3. **Instant On-Device Utilities**: Combines local neural inference with fast cryptographic and perceptual algorithms (Shannon entropy, dHash, SQLite FTS5) for an uninterrupted workflow.

---

## 🧠 Models Used

| Model / Pipeline Component | Architecture & Details | Runtime / Optimization | Purpose in SnipSense |
|---|---|---|---|
| **DBNet (Differentiable Binarization)** | Quantized Convolutional Neural Network for real-time text detection | Embedded ONNX Runtime (`rapidocr-onnxruntime`) | Pinpoints bounding polygons `(x, y, w, h)` for all text regions across high-DPI displays in <150ms. |
| **CRNN (Convolutional Recurrent Neural Network)** | Deep text recognizer utilizing CTC loss for variable-length text decoding | Embedded ONNX Runtime (`rapidocr-onnxruntime`) | Transcribes detected image regions into structured UTF-8 characters and multi-line text strings. |
| **Shannon Entropy Token Classifier** | Statistical entropy calculation ($H(X) = -\sum P(x) \log_2 P(x)$) combined with regex heuristics | Pure Python / In-Process algorithmic | Flags high-entropy strings ($H \ge 4.2$) as potential cryptographic tokens, API keys, or private keys. |
| **Luhn Mathematical Validator** | Modulo 10 checksum algorithm | In-Memory native computation | Distinguishes actual credit/debit card numbers from arbitrary 13–19 digit numeric sequences to prevent false positives. |
| **dHash (Difference Hash)** | 64-bit gradient perceptual image hashing | `Pillow` & `NumPy` array operations | Groups rapid burst screenshots and near-identical windows into duplicate clusters using Hamming distance ($\le 10$). |

---

## 🛠️ Technologies and Frameworks

* **Core Runtime**: Python 3.9+ (Full PEP 563 / PEP 604 compatibility)
* **GUI & Presentation Layer**: `PyQt6` (Hardware-accelerated rendering, translucent frameless canvases, global shortcuts, and custom Dark Theme QSS matching modern UI standards)
* **Computer Vision & Image Processing**: `Pillow` (PIL) & `OpenCV` (`opencv-python` for H.264 video encoding and pixel-level transformations)
* **In-Process Neural Inference**: `rapidocr-onnxruntime` (`onnxruntime` CPU engine)
* **Storage & Visual Memory**: Embedded `SQLite 3` with `FTS5` (Full-Text Search virtual table, porter tokenization, BM25 relevance ranking)
* **Screen Frame Capture Engine**: `mss` (Direct OS frame-buffer capture with sub-10ms multi-monitor virtual desktop support)
* **Input & Hotkey Subsystem**: Native Cocoa monitor (`AppKit` on macOS) & `pynput` (Windows / Linux)
* **Test Suite**: `pytest` & `pytest-qt` (80 automated unit, integration, and UI component tests)

---

## ☁️ APIs and Cloud Services

> **Crucial Hackathon Statement**: **NONE.**

* **No Cloud Vision APIs** (No Google Cloud Vision, AWS Rekognition, or Azure Cognitive Services)
* **No Large Language Model APIs** (No OpenAI GPT-4o, Anthropic Claude, or remote endpoints)
* **No Analytics / No Telemetry** (No Sentry, Google Analytics, or remote tracking beacons)

Every algorithm, model weight, and indexing mechanism is bundled and executed directly on the host operating system.

---

## 📦 Existing Code and Open-Source Assets

SnipSense proudly stands on the shoulders of battle-tested open-source libraries:

* **[rapidocr-onnxruntime](https://github.com/RapidAI/RapidOCR)**: Embedded ONNX-based text detection (DBNet) and recognition (CRNN) models.
* **[PyQt6](https://riverbankcomputing.com/software/pyqt/)**: Cross-platform GUI framework and event loop.
* **[mss](https://github.com/BoboTiG/python-mss)**: Ultra-fast multi-monitor cross-platform screen grabber.
* **[Pillow](https://python-pillow.org/)**: Image processing, color quantization, and animated GIF synthesis.
* **[opencv-python](https://github.com/opencv/opencv-python)**: Video encoding pipeline for screen clips.
* **[pynput](https://github.com/moses-palmer/pynput)**: Cross-platform keyboard event listener.

---

## 🤖 AI Development Tools

To rapidly architect, code, test, and polish SnipSense for the AppBuildersPH 2026 Hackathon, the team utilized:

* **Antigravity AI (Google DeepMind)**: Used for architecture design, agentic pair programming, test-driven development (TDD), and cross-platform Cocoa/PyQt6 debugging.
* **Claude 3.7 Sonnet & Opus / Gemini 2.5 Pro**: Utilized for real-time edge-case stress-testing, regular expression security rules, and performance optimization of perceptual hashing algorithms.

---

## ✨ Features & User Surfaces

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               SNIPSENSE USER SURFACES                                  │
├───────────────────────────────┬───────────────────────────────┬────────────────────────┤
│ 1. Precision Selection Canvas │ 2. Interactive Preview Dialog │ 3. Frosted-Glass HUD   │
│    • Multi-monitor virtual    │    • Interactive OCR boxes    │    • Alt + Z launcher  │
│      desktop freeze           │    • Click-to-copy snippets   │    • Recent captures   │
│    • Dimension pill & handles │    • 🛡️ PII Mask / Unmask      │    • Telemetry badges  │
├───────────────────────────────┼───────────────────────────────┼────────────────────────┤
│ 4. Search Vault (Alt + F)     │ 5. Duplicate Cleaner          │ 6. Recording Pill      │
│    • SQLite FTS5 prefix query │    • dHash perceptual clusters│    • 15-20 FPS capture │
│    • <50ms instant response   │    • Side-by-side comparison  │    • 30s auto-cap      │
│    • Bold matched snippets    │    • Safe batch archive & undo│    • MP4 / GIF export  │
└───────────────────────────────┴───────────────────────────────┴────────────────────────┘
```

---

## 🚀 Installation & Getting Started

### Prerequisites
* Python **3.9** or newer (Tested on macOS, Windows, Linux)
* `pip` and `git`

### 1. Clone the Repository
```bash
git clone https://github.com/hubertsangil/snip-sense.git
cd snip-sense
```

### 2. Create and Activate a Virtual Environment
```bash
# On macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate

# On Windows:
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run SnipSense
```bash
python main.py
```

### 5. Run the Automated Test Suite
```bash
pytest -v
```
*(Runs all 80 automated unit & UI tests across capture, OCR, privacy shield, search vault, deduplication, and screen recorder)*

---

## ⌨️ Global Shortcuts

| Shortcut | Action | Description |
|---|---|---|
| `Ctrl + Shift + S` / `Cmd + Shift + S` | **New Screen Snip** | Freezes all displays, launches selection marquee, extracts OCR, and suggests auto-name. |
| `Alt + Z` | **Summon Overlay HUD** | Opens translucent frosted-glass launcher with quick actions and recent captures carousel. |
| `Alt + F` | **Search Vault** | Opens Spotlight-style full-text search across all past screenshots and OCR text. |
| `Ctrl + Shift + R` | **Record Screen Clip** | Spawns floating recording pill to capture up to 30s of video exported as MP4 & GIF. |
| `ESC` | **Dismiss / Cancel** | Seamlessly cancels current snip, search, HUD, or recording. |

---

## 👥 Meet the Team (Richeese)

Developed with passion for **AppBuildersPH 2026 Hackathon**:

* **Hubert Ross O. San Gil**
* **Denrei Samual M. Angeles**
* **Ritzy Leewis G. Celestial**
* **Genesis Jim C. Cuasay**

---

## 📄 License

This project is open-source and licensed under the [MIT License](LICENSE).
