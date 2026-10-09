# 04: Hybrid Auto-Naming & Instant File Saving

**What to build:** When a capture is taken, SnipSense automatically infers a human-readable, descriptive filename (such as `VSCode_Docker_Exit137.png` or `Chrome_Amazon_Order114.png`) instead of generic operating system timestamps. It achieves this by reading the active foreground window title at the time of capture, paired with the top OCR headline text. The suggested name is displayed in the preview toolbar, where the user can click to edit or hit "Save" (or `Ctrl+S`) to commit the file to disk instantly.

**Blocked by:** 02: In-Process OCR & Interactive Text Bounding Boxes

**Status:** completed

- [x] At the moment of capture, the active foreground window title is queried via system APIs in under 5ms.
- [x] The engine inspects dominant, high-confidence OCR text lines and combines them with the application context to synthesize a clean, sanitized slug (e.g., `AppName_DominantKeyword_Date.png`).
- [x] If an optional bundled micro-SLM (`Qwen2.5-0.5B`) is available, it optionally enriches the title; if unavailable, the heuristic pipeline completes cleanly without warnings or errors.
- [x] The suggested filename is presented in an editable text field on the preview toolbar.
- [x] Clicking "Save" (or pressing `Enter` / `Ctrl+S`) writes the file to the user's configured captures directory.
- [x] Special filesystem characters (`/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`) are strictly sanitized to prevent filesystem errors.
