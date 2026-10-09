# 05: Persistent Visual Memory Database & Instant Full-Text Search

**What to build:** Every capture saved or processed by SnipSense is automatically indexed into an embedded SQLite database utilizing the FTS5 full-text search virtual table. A dedicated search launcher (triggered via `Alt + F` or from the toolbar) provides an instant search bar. As the user types queries (such as *"flight confirmation"*, *"wifi password"*, or *"syntax error"*), matching screenshots appear in a responsive grid in under 50ms, with query terms highlighted on the image thumbnail and an instant "Copy Text" action.

**Blocked by:** 04: Hybrid Auto-Naming & Instant File Saving

**Status:** ready-for-agent

- [ ] Embedded SQLite schema initializes automatically with an `fts_captures` virtual table indexing `title`, `ocr_text`, `tags`, and `file_path`.
- [ ] Every saved capture is ingested into the database transactionally without blocking the UI thread.
- [ ] Pressing `Alt + F` (or clicking a search icon) summons a clean, fast visual search modal.
- [ ] Search input performs real-time FTS5 prefix queries and ranks results by relevance and recency.
- [ ] Results display image thumbnails, matching title, capture timestamp, and highlighted matching text snippets.
- [ ] Clicking a search result card opens its full preview with options to copy text, copy image, or open the original file location.
