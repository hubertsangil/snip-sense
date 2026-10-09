# 08: Short GIF / MP4 Clip Screen Recorder

**What to build:** From the HUD overlay or via a quick recording shortcut, the user can record up to 30 seconds of screen activity for demonstrating bugs or UI interactions. A discreet, floating recording pill with a flashing indicator and timer (e.g., `🔴 00:14 / 00:30 [Stop]`) appears during capture. Upon stopping, the frames are encoded into an optimized, silent animated GIF or MP4 file, automatically named based on the foreground application context, and copied or saved directly for sharing in Slack, Discord, or GitHub issues.

**Blocked by:** 07: Frosted-Glass Overlay HUD (`Alt + Z`)

**Status:** ready-for-agent

- [ ] "Record Clip" action initiates a non-blocking background frame capture loop at ~15-20 FPS using `mss`.
- [ ] A lightweight, draggable floating recording pill displays live elapsed time, recording status indicator, and a "Stop" button.
- [ ] Recording automatically caps at 30 seconds if the user does not manually stop it beforehand.
- [ ] Captured frames encode into both silent animated GIF and H.264 MP4 formats using bundled `imageio` / `imageio-ffmpeg`.
- [ ] Generated recording is automatically given a descriptive name (e.g., `Chrome_Checkout_Repro.mp4` or `.gif`).
- [ ] A completion banner offers immediate actions: "Copy File", "Open Folder", or "Preview".
- [ ] Output files are optimized for size (under 10MB) to ensure seamless upload to Discord, Slack, and GitHub.
