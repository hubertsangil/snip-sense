# 06: Historical Screenshot Ingestion & Perceptual Deduplication

**What to build:** On initial startup or upon user demand, SnipSense scans the local system's default screenshot repository (e.g., `Pictures/Screenshots`), computes perceptual hashes (`imagehash` dHash/aHash) for each file, and ingests them into the SQLite database. Screenshots with a Hamming distance $\le 4$ are tagged as duplicate clusters (e.g., rapid bursts or identical error captures). The UI displays a notification showing how many past screenshots were indexed, how many duplicates were found, and provides a 1-click "Clean Duplicates" action to safely archive or remove redundant copies while retaining the best version.

**Blocked by:** 05: Persistent Visual Memory Database & Instant Full-Text Search

**Status:** ready-for-agent

- [ ] Background thread detects standard OS screenshots directories (`Pictures/Screenshots` or user-configured folder) without blocking UI startup.
- [ ] Historical images (`.png`, `.jpg`, `.jpeg`, `.webp`) are parsed, hashed with `imagehash`, and indexed into SQLite FTS5.
- [ ] Duplicate detection algorithm groups images with Hamming distance $\le 4$ under the primary/earliest capture.
- [ ] System surfaces a status badge: *"X past screenshots indexed | Y duplicate bursts detected"*.
- [ ] A "Review & Clean Duplicates" view presents side-by-side comparisons of detected duplicate sets.
- [ ] 1-click batch cleanup moves redundant duplicates to a designated trash/archive folder with complete safety and undo capability.
