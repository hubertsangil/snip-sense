# SnipSense Brand Guidelines — Direction A: The Obsidian Razor

## 1. Brand Essence & Positioning
- **Brand Name**: SnipSense
- **Tagline**: The AI-Native Desktop Snipping & Privacy Companion
- **Aesthetic Philosophy**: High-precision monochrome luxury merging Raycast/Linear developer minimalism with GeForce HUD fluidity.

---

## 2. The Mark — Anatomy & Meaning
The SnipSense mark is a **Precision Pictorial Letterform Fusion**:
- **The "Snip" (Cutting Action)**: Symmetrical 45° razor-blade shears constructed on mathematical arcs and clean 45° angles.
- **The "Sense" (Optical Intelligence)**: A central optical sensor aperture representing 100% offline OCR vision and privacy shielding.
- **The Monogram**: Subtle optical `S` letterform silhouette when viewed as a whole.

---

## 3. Color Tokens

| Role | Color Name | Hex Code | Purpose |
| :--- | :--- | :--- | :--- |
| **Primary Brand Dark** | Obsidian Base | `#0B0D10` | Master symbol, app background, primary typography |
| **Surface Dark** | Studio Surface | `#14181F` | Elevated card surfaces, floating HUD backdrop |
| **Primary Brand Light**| Studio White | `#FFFFFF` | Inverted logo mark, dark-mode headlines |
| **Subtle Slate** | Slate Muted | `#94A3B8` | Secondary labels, hotkeys, metadata |
| **Accent Glow** | Cyber Cyan | `#38BDF8` | Central sensor eye / optical focal point |
| **Accent Indigo** | Electric Indigo| `#6366F1` | UI active states, focus borders, secondary branding |

---

## 4. Minimum Sizing & Clear Space
- **Clear Space**: Always maintain a clear margin equal to at least half the width of one handle ring ($0.25 \times \text{size}$) around the mark.
- **Minimum Digital Size**: 
  - Standalone Symbol: **16 × 16 px** (tested and verified for macOS Menu Bar tray).
  - Horizontal Lockup: **24 px height** / minimum width 80 px.

---

## 5. Asset Hierarchy (`branding/direction-a/`)

```
branding/direction-a/
├── masters/
│   ├── symbol-obsidian.svg          # Master 1-color black/obsidian vector
│   ├── symbol-white.svg             # Master 1-color inverted white vector
│   ├── symbol-accent.svg            # Master Indigo + Cyber Cyan sensor vector
│   ├── lockup-horizontal-obsidian.svg # Horizontal lockup (Obsidian on white)
│   ├── lockup-horizontal-white.svg    # Horizontal lockup (White on obsidian)
│   ├── lockup-horizontal-accent.svg   # Horizontal lockup with glowing accent
│   └── app-icon-dark.svg            # macOS Squircle container master
│
├── icons/                           # Complete production multi-res suite
│   ├── favicon.ico                  # Multi-resolution ICO (16/32/48)
│   ├── favicon.svg                  # Vector SVG favicon
│   ├── site.webmanifest             # PWA web manifest
│   ├── apple-touch-icon.png         # iOS / Touch icon (180x180)
│   ├── symbol-obsidian-app-icon-*.png (16px, 32px, 64px, 128px, 256px, 512px, 1024px)
│   └── symbol-obsidian-black-*.png    (Transparent PNGs)
│
├── preview-sheet.html               # Interactive browser QA test sheet
└── preview-sheet.png                # Multi-scale rendering validation
```
