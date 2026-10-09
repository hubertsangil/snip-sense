# 01: Interactive Screen Snip & Instant Preview Canvas

**What to build:** The user can press a hotkey (or trigger a capture action) to freeze the screen under a semi-transparent, frameless selection canvas. By clicking and dragging the mouse, the user selects a region of the screen. Upon releasing the mouse, the selected region is captured in sub-10ms and immediately presented in an interactive preview window equipped with a "Copy Image" button that writes the bitmap to the clipboard.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Pressing the capture shortcut summons a responsive, full-screen transparent selection canvas across all active displays.
- [ ] Dragging the mouse renders a visual selection rectangle with real-time coordinate and dimension indicators.
- [ ] Releasing the mouse captures the exact pixel buffer inside the rectangle using fast in-memory capture (`mss`).
- [ ] The captured image immediately opens in an interactive desktop preview window anchored near the cursor or centered.
- [ ] Clicking "Copy Image" places the full-resolution captured image onto the OS system clipboard.
- [ ] Pressing `ESC` at any point during selection cleanly dismisses the canvas without side effects.
