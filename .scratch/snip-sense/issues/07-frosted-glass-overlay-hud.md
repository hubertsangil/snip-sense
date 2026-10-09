# 07: Frosted-Glass Overlay HUD (`Alt + Z`)

**What to build:** The user can press `Alt + Z` anywhere in Windows (including over games and full-screen applications) to summon an elegant, translucent, frosted-glass HUD overlay. The HUD displays a top-tier action bar ([Snip Area], [Record Clip], [Search Vault], [Clean Duplicates]) and a smooth horizontal carousel of recent captures with badges showing their PII masking status, auto-generated title, and quick-action buttons ([Copy Image], [Copy Text], [Open]). Pressing `ESC` or clicking outside dismisses the HUD seamlessly.

**Blocked by:** 05: Persistent Visual Memory Database & Instant Full-Text Search, 06: Historical Screenshot Ingestion & Perceptual Deduplication

**Status:** ready-for-agent

- [ ] Global hotkey listener (`keyboard` / `pynput`) reliably captures `Alt + Z` across all foreground applications.
- [ ] HUD renders as a frameless, semi-transparent backdrop with modern dark-mode card styling and subtle glassmorphic effects.
- [ ] Top action bar features quick-trigger buttons:
  - ✂️ Snip Area (`Ctrl+Shift+S`)
  - ⏺️ Record Clip
  - 🔍 Search Visual Memory (`Alt+F`)
  - 🧹 Clean Duplicates (with dynamic badge showing duplicate count)
- [ ] Displays a scrollable horizontal carousel of the last 10 captures with generated thumbnails, timestamps, and PII status badges.
- [ ] Clicking any card in the carousel allows instant clipboard copying or full inspection.
- [ ] Pressing `ESC` or clicking the backdrop smoothly closes the HUD and returns focus to the previous active window.
