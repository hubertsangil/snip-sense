# DESIGN.md — SnipSense Native UI & UX Blueprint

## 1. Executive Summary & Design Vision

**SnipSense** is an AI-native, privacy-first desktop screenshot and screen capture utility built with Python and PyQt6. It is engineered as a clean, precision native tool conforming to modern Windows 11 Fluent Design principles (Mica dark palette, subtle elevation, restrained typography, and functional keyboard shortcuts).

### 1.1 Aesthetic Philosophy
The visual language adheres to:
1. **Native Desktop Utility Precision:** Windows 11 Fluent dark surfaces (`#202020` Mica base), subtle elevation dividers (`#383838`), restrained typography (`Segoe UI Variable Text`), and functional keyboard shortcuts.
2. **Restraint Over Novelty:** Zero decorative emojis, zero aggressive saturated gradients, and zero web-like toy styling. Icons and indicators are purpose-built, legible, and consistent with native operating system chrome.
3. **Ambient HUD Utility (`Alt + Z`):** A non-intrusive overlay floating cleanly over active windows, games, and code editors without requiring context switching.

### 1.2 Core UX Principles
- **Sub-Second Perceived Latency:** Every user action (capture, OCR box rendering, PII masking, file naming) responds in under 100ms.
- **Privacy as a Visible Guarantee:** Sensitive data redaction highlights exact bounding boxes with clean visual masks and an authentic offline status badge.
- **Zero Friction Context Anchoring:** Clean action dock and frameless custom window containers provide full control with native dragging, minimize, maximize, and exit behaviors.
- **Graceful Non-Destructive Actions:** Auto-actions (naming, deduplication, blurring) always provide instant manual overrides, inline editing, and 1-click undo.

---

## 2. Design Tokens & System Foundation

### 2.1 Color Palette
The color system uses refined Windows 11 Fluent dark neutrals paired with system blue accent:

| Token Name | Hex Code | Semantic Role |
| :--- | :--- | :--- |
| `--bg-base` | `#202020` | Root background for windows and dialog shells |
| `--bg-surface` | `#262626` | Surface color for toolbars, dialogs, cards |
| `--bg-surface-elevated`| `#2D2D2D` | Hover states, elevated card surfaces |
| `--bg-recessed` | `#1A1A1A` | Input fields, preview frames, scroll backgrounds |
| `--border-subtle` | `#383838` | Window outlines, card borders, dividers |
| `--border-subtle-trans` | `rgba(255, 255, 255, 0.08)` | Hairline elevation borders |
| `--accent-primary` | `#0067C0` | Primary action button fill, active selection |
| `--accent-hover` | `#1170CF` | Primary button hover state |
| `--accent-focus` | `#0078D4` | Focus outline and active border highlights |
| `--text-primary` | `#F3F3F3` | Primary headlines, active text, button labels |
| `--text-secondary` | `#A0A0A0` | Subtitles, timestamps, hotkey badges, metadata |
| `--text-muted` | `#767676` | Inactive placeholders, disabled actions |
| `--accent-close-hover` | `#C42B1C` | Windows standard close button hover background |

### 2.2 Typography Scale
Built for standard Windows native system fonts: `'Segoe UI Variable Text', 'Segoe UI', system-ui, sans-serif`.

| Role | Size | Weight | Line Height | Tracking |
| :--- | :--- | :--- | :--- | :--- |
| **Window Title** | 12px | 600 (SemiBold) | 16px | 0 |
| **Section Header** | 13px | 600 (SemiBold) | 18px | 0 |
| **Body Standard** | 13px | 400 (Regular) | 18px | 0 |
| **Body Medium** | 12px | 500 (Medium) | 16px | 0 |
| **Caption / Shortcut** | 11px | 500 (Medium) | 14px | 0 |
| **Monospace Time** | 13px | 600 (SemiBold) | 16px | 0 |

### 2.3 Geometry & Elevation
- **Border Radii:**
  - Micro-pills / Badges: `4px`
  - Toolbar buttons / Inputs: `6px`
  - Cards & Containers: `6px`
  - Window Containers: `8px`
- **Elevation Shadows:**
  - Window Container: `0 8px 24px rgba(0, 0, 0, 0.35), 0 0 0 1px rgba(255, 255, 255, 0.06)`
  - HUD Overlay Container: `0 16px 40px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.08)`

---

## 3. Visual Component Library

### 3.1 Buttons
- **Primary Action (Windows Accent):** High-contrast button for "New Capture", "Save", and "Stop & Save". Solid `#0067C0` with white `#FFFFFF` text and 6px border-radius.
- **Secondary Ghost Action:** Subtle `#2D2D2D` fill with `#F3F3F3` text and `#383838` border. Hover shifts to `#383838`.
- **Window Controls (Title Bar):** Fixed 38×30px rectangular control buttons (Minimize `—`, Expand `□` / `❐`, Close `✕`). Close button transitions to `#C42B1C` on hover.

### 3.2 Badges & Status Pills
- **Offline Assurance Badge:** `[ 100% Offline ]` — Subtle pill (`rgba(255, 255, 255, 0.06)`) confirming zero cloud egress.
- **Text Block Count Badge:** `[ 3 text blocks detected ]` — Quiet status pill in the inspector header.
- **Hotkey Capsule:** Clean right-aligned shortcut indicators (`Ctrl+Shift+S`, `Alt+F`) with crisp contrast.

---

## 4. Screen & Surface Blueprints

### Surface 1: The Full-Screen Snipping Canvas (`SnipCanvas`)
When triggered (`Ctrl+Shift+S`), this frameless window covers all monitors.
- **Dimming Layer:** `rgba(0, 0, 0, 0.42)` overlay darkening unselected areas.
- **Dimension Pill:** Dynamic pill following cursor showing selection dimensions (`W × H px`).
- **Corner Handles:** Four clean 6×6px white corner anchors indicating selection marquee.

### Surface 2: Main Studio Launcher (`ControlWindow`)
- **Title Bar:** Custom borderless titlebar with brand title, offline badge, and dedicated minimize, expand, exit controls.
- **Primary Command:** Authoritative full-width `New Capture` button with right-aligned `Ctrl+Shift+S` shortcut pill.
- **Quick Action Grid:**
  - `Record Screen` (`Ctrl+Shift+R`)
  - `Overlay HUD` (`Alt+Z`)
  - `Search Vault` (`Alt+F`)
  - `Clean Duplicates`
- **Footer:** `Open Folder` button with quiet tray indicator: `Runs in system tray when closed`.

### Surface 3: Capture Inspector Dialog (`PreviewWindow`)
- **Header:** Clean `Capture Inspector` title, detection count status badge, and close button.
- **Image Viewport:** High-contrast dark canvas displaying the captured frame and interactive OCR bounding boxes.
- **Save Row:** Filename input box (`Save As:`) with `Save` (`Ctrl+S`) and `Open Folder` actions.
- **Action Dock:** `Redact PII`, `Text Boxes` toggle, `Copy All Text`, `Copy Image`, `Close`.

### Surface 4: Overlay HUD (`OverlayHUD` - `Alt + Z`)
- **Quick Launch Bar:** Clean action buttons: `New Capture`, `Record Screen`, `Search Vault`, `Clean Duplicates`.
- **Recent Captures Carousel:** Horizontal scrollable row displaying recent capture cards with clean `Image`, `Text`, `Redacted` pills and action buttons (`Image`, `Text`, `Open`).
- **Footer:** Clean index status telemetry (`142 captures indexed • Local database`).

### Surface 5: Visual Memory Search Dialog (`SearchModal` - `Alt + F`)
- **Search Bar:** Input with placeholder `Search captured text, titles, or tags... (Esc to close)`.
- **Results List:** Clean `SearchResultCard` items with thumbnail, relative timestamp, highlighted `<mark>` text matches, and `Copy Text` / `Open` action buttons.

### Surface 6: Screen Clip Recording Pill (`RecorderPill`)
- **Floating Pill:** Draggable frameless floating widget with pulsing `🔴 REC` indicator, monospace timer (`00:14 / 00:30`), `Stop & Save`, and `✕` cancel button.
