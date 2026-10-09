#!/usr/bin/env python3
"""Render video/overview.html into assets/overview.mp4, assets/overview.webm and assets/overview-poster.jpg.

Frame-exact: the page exposes render(t); we step t at FPS, screenshot each frame with Playwright's
Chromium, and let ffmpeg encode. Needs: pip install playwright (plus a Chromium), and ffmpeg on PATH.
"""
import os, shutil, subprocess, sys, tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FPS = 30
POSTER_AT = 7.4          # the riddle scene, two seconds in
CHROME = os.environ.get("CHROME_PATH")   # optional: an explicit chrome-headless-shell binary

def main() -> None:
    frames = Path(tempfile.mkdtemp(prefix="qct-frames-"))
    with sync_playwright() as p:
        kw = {"executable_path": CHROME} if CHROME else {}
        browser = p.chromium.launch(**kw)
        page = browser.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=1)
        page.goto((ROOT / "video" / "overview.html").as_uri())
        page.evaluate("document.body.classList.add('capture')")
        page.wait_for_timeout(300)
        duration = page.evaluate("window.DURATION")
        total = int(duration * FPS)
        for i in range(total):
            page.evaluate("t => render(t)", i / FPS)
            page.screenshot(path=str(frames / f"f{i:05d}.png"), clip={"x": 0, "y": 0, "width": 1280, "height": 720})
            if i % (FPS * 5) == 0:
                print(f"{i}/{total} frames", flush=True)
        page.evaluate("t => render(t)", POSTER_AT)
        page.screenshot(path=str(ROOT / "assets" / "overview-poster.jpg"), type="jpeg", quality=88, clip={"x": 0, "y": 0, "width": 1280, "height": 720})
        browser.close()
    common = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-framerate", str(FPS), "-i", str(frames / "f%05d.png")]
    subprocess.run(common + ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "slow", "-movflags", "+faststart", str(ROOT / "assets" / "overview.mp4")], check=True)
    subprocess.run(common + ["-c:v", "libvpx-vp9", "-pix_fmt", "yuv420p", "-crf", "32", "-b:v", "0", "-row-mt", "1", str(ROOT / "assets" / "overview.webm")], check=True)
    shutil.rmtree(frames)
    for f in ("overview.mp4", "overview.webm", "overview-poster.jpg"):
        print(f, f"{(ROOT / 'assets' / f).stat().st_size / 1e6:.1f} MB")

if __name__ == "__main__":
    main()
