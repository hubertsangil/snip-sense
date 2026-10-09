# 02: In-Process OCR & Interactive Text Bounding Boxes

**What to build:** When a screenshot is captured, it is immediately and automatically processed in-process by an embedded OCR engine (`rapidocr-onnxruntime`) without contacting external servers or requiring system binary installs. The recognized text blocks and their bounding boxes are displayed over the preview window. The user can hover over any text line to see its recognized text, click an individual box to copy that snippet to the clipboard, or click a "Copy All Text" button to copy the entire extracted text block.

**Blocked by:** 01: Interactive Screen Snip & Instant Preview Canvas

**Status:** ready-for-agent

- [ ] Every captured image is processed through in-process `RapidOCR` in under 80ms on standard CPU.
- [ ] OCR returns accurate character/word bounding polygons, normalized coordinates `(x, y, w, h)`, and text strings.
- [ ] Bounding boxes are rendered as subtle visual overlays atop the preview image.
- [ ] Hovering over a bounding box displays a tooltip with the recognized text string.
- [ ] Clicking any individual bounding box copies its exact text string directly to the OS clipboard and displays a brief visual confirmation.
- [ ] A "Copy All Text" button on the toolbar extracts and concatenates all detected lines into structured text on the clipboard.
- [ ] Captures with no detected text degrade gracefully without errors or visual artifacts.
