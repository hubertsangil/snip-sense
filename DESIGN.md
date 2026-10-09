# DESIGN.md — SnipSense UI & UX Blueprint

## 1. Executive Summary & Design Vision

**SnipSense** is an AI-native, privacy-first desktop screenshot and screen capture companion built with Python and PyQt6. It is designed to replace default OS snipping utilities with an experience that feels instantaneous, intelligent, and protective of user privacy.

### 1.1 Aesthetic Philosophy
The visual language merges two proven design archetypes:
1. **Raycast / Linear Professional Minimalism:** Clean dark-mode surfaces, crisp borders, subtle elevation, restrained typography, and functional keyboard-driven shortcuts.
2. **NVIDIA GeForce Experience / AMD Adrenalin HUD Fluidity:** An ambient, non-intrusive `Alt + Z` frosted-glass overlay that floats seamlessly over active windows, games, and code editors without forcing the user to switch application contexts.

### 1.2 Core UX Principles
- **Sub-Second Perceived Latency:** Every user action (capture, OCR box rendering, PII masking, file naming) must respond in under 100ms.
- **Privacy as a Visible Guarantee:** Sensitive data masking is not a hidden background guess; users see exact bounding boxes, clear visual masks, and an ambient "100% Offline" security badge.
- **Zero Friction Context Anchoring:** Menus and toolbars appear exactly where the user is already looking—directly next to the cursor upon crop release.
- **Graceful Non-Destructive Actions:** Auto-actions (naming, deduplication, blurring) always provide instant manual overrides, inline editing, and 1-click undo.

---

## 2. Design Tokens & System Foundation

### 2.1 Color Palette
The color system uses deep neutral zinc tones paired with an emerald green privacy accent and deliberate status signals:

| Token Name | Hex Code | Semantic Role |
| :--- | :--- | :--- |
| `--bg-base` | `#0B0D10` | Root background for overlays and backdrops |
| `--bg-surface` | `#14181F` | Surface color for toolbars, dialogs, cards |
| `--bg-surface-elevated`| `#1D232D` | Hover states, elevated card surfaces |
| `--border-subtle` | `#262E3B` | Card outlines, dividers, inactive bounding boxes |
| `--border-accent` | `#3B82F6` | Active crop marquee selection, focused inputs |
| `--text-primary` | `#F1F5F9` | Primary headlines, active text, button labels |
| `--text-secondary` | `#94A3B8` | Subtitles, timestamps, hotkey badges, metadata |
| `--text-muted` | `#64748B` | Inactive placeholders, disabled actions |
| `--accent-emerald` | `#10B981` | Privacy Shield active, 100% offline badge, safe state |
| `--accent-amber` | `#F59E0B` | Duplicate burst warning, expiring item, pending edit |
| `--accent-rose` | `#F43F5E` | Redacted text mask, recording indicator, cancel button |
| `--mask-gaussian` | `rgba(244,63,94,0.18)` | Visual fill for masked bounding box in edit mode |

### 2.2 Typography Scale
Built for standard system fonts: `Segoe UI` (Windows native default) with graceful fallback to `Inter`, `SF Pro Display`, or `system-ui`.

| Role | Size | Weight | Line Height | Tracking |
| :--- | :--- | :--- | :--- | :--- |
| **Display Title** | 20px | 700 (Bold) | 28px | -0.02em |
| **Section Header** | 15px | 600 (SemiBold) | 22px | -0.01em |
| **Body Standard** | 13px | 400 (Regular) | 18px | 0 |
| **Body Medium** | 13px | 500 (Medium) | 18px | 0 |
| **Caption / Hotkey**| 11px | 600 (SemiBold) | 14px | +0.02em |
| **Coordinate Monospace**| 12px | 500 (Mono) | 16px | 0 |

### 2.3 Geometry & Elevation
- **Border Radii:**
  - Micro-pills / Hotkey badges: `4px`
  - Toolbar buttons / Inputs: `8px`
  - Floating mini-toolbar: `10px`
  - HUD cards & Dialogs: `14px`
- **Elevation Shadows:**
  - Mini-Toolbar: `0 8px 32px rgba(0, 0, 0, 0.45), 0 0 0 1px rgba(255, 255, 255, 0.08)`
  - HUD Overlay Container: `0 16px 48px rgba(0, 0, 0, 0.65), 0 0 0 1px rgba(255, 255, 255, 0.1)`

---

## 3. Visual Component Library

### 3.1 Buttons
- **Primary Action (Emerald / Accent):** High-contrast button for "Shield PII" and "Save". Solid emerald `#10B981` with dark `#0B0D10` text for maximum visual pop.
- **Secondary Ghost Action:** Subtle `#1D232D` fill with `#F1F5F9` text and `#262E3B` border. On hover, background shifts to `#2A3342`.
- **Icon-Only Utility Button:** 32×32px square button with rounded corners (`6px`), housing icons like Copy, Edit, Trash, or Settings.

### 3.2 Badges & Status Pills
- **Privacy Badge:** `[ 🛡️ PII Masked ]` — Green tint background (`rgba(16, 185, 129, 0.15)`), green border, green text.
- **Offline Assurance Badge:** `[ 🟢 100% Offline ]` — Persistent indicator reassuring users that no data leaves local memory.
- **Duplicate Indicator:** `[ 🧹 3 Duplicates ]` — Amber pill badge alerting user to redundant captures.
- **Hotkey Capsule:** Small dark pill `[ Ctrl+C ]` with `#94A3B8` monospace text displayed alongside menu actions.

---

## 4. Screen & Surface Blueprints

### Surface 1: The Full-Screen Snipping Canvas (`SnipCanvas`)
When triggered (`Win+Shift+S` or `Ctrl+Shift+S`), this frameless window covers all monitors.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Screen dimmed with rgba(0, 0, 0, 0.42)                                       │
│                                                                             │
│               [+] Mouse Crosshair Cursor                                    │
│                │                                                            │
│                ▼                                                            │
│         ┌──────────────────────────────────────┐                            │
│         │ Selected Crop Area (Clear / Unmasked)│  [ 840 × 420 px ]          │
│         │                                      │  (Floating dimension badge)│
│         │ Active 1.5px dashed border: #3B82F6   │                            │
│         └──────────────────────────────────────┘                            │
│                                                                             │
│ Press ESC to cancel                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

- **Dimming Layer:** `rgba(0, 0, 0, 0.42)` overlay darkening non-selected areas to focus the user's eye.
- **Dimension Pill:** Dynamic 12px pill following the cursor showing real-time selection dimensions (`W × H`).
- **Corner Handles:** Four subtle 6×6px white squares at the marquee corners to indicate active selection.

---

### Surface 2: The Contextual Mini-Toolbar (`MiniToolbar`)
Immediately upon releasing the mouse drag, the mini-toolbar anchors dynamically directly below or above the crop selection (guaranteed to stay within screen boundaries).

```text
┌───────────────────────────────────────────────────────────────────────────────────┐
│ 🛡️ Shield PII │ 📋 Copy Text │ 🖼️ Copy Image │ 💾 Save │ VSCode_Error_Log.png ✎ │ ✕ │
└───────────────────────────────────────────────────────────────────────────────────┘
```

- **Height:** 42px compact height with zero wasted space.
- **Elements:**
  1. **[ 🛡️ Shield PII ]:** Primary emerald toggle button. Instantly blurs all detected emails, keys, tokens, and cards.
  2. **[ 📋 Copy Text ]:** Extracts all OCR text directly to clipboard.
  3. **[ 🖼️ Copy Image ]:** Copies the current bitmap (with applied blurs) to the clipboard and shows a "Copied!" checkmark.
  4. **[ 💾 Save ]:** Saves to disk using the suggested auto-name.
  5. **Auto-Name Slug Box:** Displays the inferred title with an inline pencil icon; clicking allows instant text editing.
  6. **Dismiss `✕`:** Closes the preview.

---

### Surface 3: Interactive OCR Bounding Box Layer (`OCRBoxOverlay`)
Visual overlays displayed directly on top of the captured image preview.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│  Error connecting to database at 192.168.1.104:5432                     │
│  User: [ admin@company.com ] ◄── (Auto-masked with Gaussian Blur)       │
│  Token: [ sk_live_83921... ] ◄── (Auto-masked with Gaussian Blur)       │
│                                                                         │
│  ┌─────────────────────────────────┐                                    │
│  │ Hover Tooltip: "admin@company.com"│                                  │
│  │ Status: Masked (Click to unmask) │                                   │
│  └─────────────────────────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

- **Normal Text State:** Transparent box with faint 1px border on hover (`#3B82F6`). Clicking copies that single line to clipboard.
- **Sensitive Detected State:** Box highlighted in subtle amber or red border.
- **Masked State:** Underlying pixels replaced with smooth Gaussian blur. A faint frosted overlay indicates the boundary.
- **Interactive Toggling:** Clicking any box instantly toggles between blurred $\leftrightarrow$ unblurred state in under 5ms.

---

### Surface 4: The Frosted-Glass Overlay HUD (`OverlayHUD` - `Alt + Z`)
Summoned anytime via `Alt + Z`. Renders a semi-transparent dark backdrop over the entire display with centered quick-access panels.

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  🔮 SNIPSENSE                      [ 🟢 100% Offline | Zero Cloud ]        [ ESC to Close ] │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   QUICK ACTIONS:                                                                        │
│   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│   │ ✂️  Snip Area     │  │ ⏺️  Record Clip   │  │ 🔍 Search Vault  │  │ 🧹 Clean Dups   │ │
│   │   (Ctrl+Shift+S) │  │   (Up to 30s)    │  │     (Alt + F)    │  │   (3 found)     │ │
│   └──────────────────┘  └──────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                                                         │
│   RECENT CAPTURES:                                           [ View All in Vault (48) ] │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│   │ [THUMBNAIL]  │  │ [THUMBNAIL]  │  │ [THUMBNAIL]  │  │ [THUMBNAIL]  │  │ ...       │ │
│   │ Amazon_Track │  │ VSCode_Error │  │ Discord_Chat │  │ Figma_Header │  │           │ │
│   │ 2m ago       │  │ 14m ago      │  │ 1h ago       │  │ 3h ago       │  │           │ │
│   │ 🛡️ Masked    │  │ 📋 Text Ready│  │ 🛡️ Masked    │  │ #design      │  │           │ │
│   │ [Copy] [Open]│  │ [Copy] [Open]│  │ [Copy] [Open]│  │ [Copy] [Open]│  │           │ │
│   └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  └───────────┘ │
│                                                                                         │
│   STATUS: 142 historical screenshots indexed • 24.5 MB reclaimed from duplicates        │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

- **Top Action Bar:** Instant launchpads for common workflows.
- **Recent Captures Carousel:** Horizontal scrollview holding rich cards with thumbnail previews, tags, and quick-action buttons.
- **Footer Telemetry:** Displays total indexed visual memory count and duplicate cleanup health.

---

### Surface 5: Visual Memory Search Dialog (`SearchModal` - `Alt + F`)
A focused search interface modeled after modern spotlight and command-palette launchers.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│  🔍 Search screenshot text, titles, or tags...            [ ESC ]       │
├─────────────────────────────────────────────────────────────────────────┤
│  RESULTS (3 matches):                                                   │
│                                                                         │
│  ┌───┐  VSCode_Postgres_Connection_Error.png                  10m ago   │
│  │IMG│  Match: "...failed to connect to 192.168.1.104:5432..."          │
│  └───┘  Actions: [ 📋 Copy Matched Text ]  [ 🖼️ Open Screenshot ]       │
│                                                                         │
│  ┌───┐  Chrome_Amazon_Order_Tracking.png                      2d ago    │
│  │IMG│  Match: "...tracking number TBA8392109482..."                    │
│  └───┘  Actions: [ 📋 Copy Matched Text ]  [ 🖼️ Open Screenshot ]       │
│                                                                         │
│  ┌───┐  Steam_DirectX_Runtime_Crash.png                       1w ago    │
│  │IMG│  Match: "...Direct3D fatal exception error code 0x800..."        │
│  └───┘  Actions: [ 📋 Copy Matched Text ]  [ 🖼️ Open Screenshot ]       │
└─────────────────────────────────────────────────────────────────────────┘
```

- **Real-Time Prefix Search:** As characters are typed, SQLite FTS5 returns matching records within 25ms.
- **Highlighted Snippets:** The search query within the OCR text snippet is highlighted in bold emerald text (`<mark>`).
- **Keyboard Navigation:** `Up` and `Down` arrow keys traverse items; pressing `Enter` opens the item; `Ctrl+C` copies the matched text immediately.

---

### Surface 6: Screen Clip Recording Pill (`RecorderPill`)
Floating widget that displays while recording an animated GIF or MP4 clip.

```text
┌───────────────────────────────────────────────────────────────┐
│  🔴 REC  00:14 / 00:30   │   [ ⏹ Stop & Save ]   │   [ ✕ ]     │
└───────────────────────────────────────────────────────────────┘
```

- **Draggable:** Can be freely repositioned anywhere on screen to stay out of the recorded area.
- **Visual Cue:** The red dot pulses on a 1-second interval (`opacity: 1.0` $\to$ `0.3`).
- **Safety Ceiling:** Automatically stops and finalizes recording upon reaching 30 seconds.

---

## 5. Interaction States & Transitions

### 5.1 Micro-Feedback & Sounds
- **Shutter Sound / Flash:** On releasing the crop drag, a subtle 60ms white opacity flash (`rgba(255, 255, 255, 0.15)` $\to$ `0.0`) provides tactile feedback confirming capture.
- **Copy Feedback:** Clicking any copy action triggers a 1.2-second state transformation: the button text changes to *"Copied!"* with a checkmark icon before returning to the original label.

### 5.2 Transition Curves
- **HUD Entrance (`Alt + Z`):** Fade and subtle scale (`opacity 0.0 -> 1.0`, `scale 0.98 -> 1.0` over 120ms with `CubicEaseOut`).
- **Mini-Toolbar Appearance:** Instant display (0ms delay) to prevent lag perception.

---

## 6. Qt Style Sheet (QSS) Implementation Guide

Below is the baseline QSS architecture to be loaded into the `QApplication`:

```css
/* SnipSense Global Dark Theme */
QWidget {
    background-color: transparent;
    color: #F1F5F9;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}

/* Floating Mini-Toolbar & Containers */
#miniToolbar, #hudContainer, #searchContainer {
    background-color: #14181F;
    border: 1px solid #262E3B;
    border-radius: 10px;
}

/* Primary Action Buttons */
QPushButton#primaryAction {
    background-color: #10B981;
    color: #0B0D10;
    font-weight: 600;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
}
QPushButton#primaryAction:hover {
    background-color: #059669;
}

/* Secondary & Ghost Buttons */
QPushButton#ghostAction {
    background-color: #1D232D;
    color: #F1F5F9;
    border: 1px solid #262E3B;
    border-radius: 6px;
    padding: 6px 12px;
}
QPushButton#ghostAction:hover {
    background-color: #2A3342;
    border-color: #3B82F6;
}

/* Search and Text Input */
QLineEdit#searchInput, QLineEdit#slugEdit {
    background-color: #0B0D10;
    border: 1px solid #262E3B;
    border-radius: 6px;
    color: #F1F5F9;
    padding: 6px 10px;
    selection-background-color: #3B82F6;
}
QLineEdit#searchInput:focus, QLineEdit#slugEdit:focus {
    border: 1px solid #3B82F6;
}

/* Tooltips */
QToolTip {
    background-color: #14181F;
    color: #F1F5F9;
    border: 1px solid #262E3B;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #0B0D10;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #262E3B;
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #3B82F6;
}
```

---

## 7. Multi-Monitor & High-DPI Handling

1. **Virtual Geometry Unification:** The snipping canvas computes the bounding union across all active screens using `QGuiApplication.screens()` and `screen.geometry()`, allowing seamless cross-monitor drag selection.
2. **Device Pixel Ratio (DPR) Scaling:** Coordinate conversion between logical widget units and physical device pixels accounts for scaling factors (e.g. 125%, 150%, 200% on Windows laptops) using `screen.devicePixelRatio()` to prevent blurred captures or misaligned bounding boxes.
3. **Screen Boundary Clamping:** The mini-toolbar position is clamped against screen edges to ensure it never renders off-screen or underneath the Windows taskbar.
