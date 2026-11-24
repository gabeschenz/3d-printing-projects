"""Render the README images from the interactive viewer.

    python render.py

Opens viewer/index.html in headless Chromium, drives it through the small
`window.kitViewer` handle the page exposes, and writes to docs/:

    render.png, render-side.png, render-top.png, render-exploded.png
    pull-apart.gif        the prop pulling apart and going back together

It reads viewer/index.html and viewer/parts.json, which build.py writes, so
run `python build.py` first (or let build.py call this for you).  Needs the packages in requirements-render.txt and a
Chromium that Playwright can launch (`playwright install chromium`).

Two environment variables cover unusual setups:

    CHROMIUM_PATH   path to a Chromium/Chrome binary to use instead of
                    Playwright's own download
    THREE_DIR       path to a local copy of the three.js 0.128 package
                    (the folder holding build/ and examples/), for machines
                    that cannot reach the CDN the viewer loads it from
"""

from __future__ import annotations

import functools
import http.server
import io
import os
import threading
from pathlib import Path

HERE = Path(__file__).parent
VIEWER = HERE / "viewer"
DOCS = HERE / "docs"

# CDN script name -> path inside a local three.js package.
THREE_FILES = {
    "three.min.js": "build/three.min.js",
    "OrbitControls.js": "examples/js/controls/OrbitControls.js",
}

STILLS = [  # (file name, view, how far pulled apart)
    ("render.png", "quarter", 0.0),
    ("render-side.png", "side", 0.0),
    ("render-top.png", "top", 0.0),
    ("render-exploded.png", "quarter", 1.0),
]

GIF_WIDTH = 760
GIF_FRAME_MS = 60
HOLD_CLOSED, MOVE, HOLD_OPEN = 8, 26, 14   # frames


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def _serve_file(path):
    """Route handler that answers a request with a local file."""
    def handler(route, request):
        route.fulfill(path=str(path), content_type="text/javascript")
    return handler


def _ease(t):
    return t * t * (3 - 2 * t)


def _animation_steps():
    """How far apart the prop is on each frame: closed, opening, open, closing."""
    steps = [0.0] * HOLD_CLOSED
    steps += [_ease(i / MOVE) for i in range(1, MOVE + 1)]
    steps += [1.0] * HOLD_OPEN
    steps += [1 - _ease(i / MOVE) for i in range(1, MOVE + 1)]
    return steps


def _write_gif(frames, path):
    from PIL import Image

    height = round(frames[0].height * GIF_WIDTH / frames[0].width)
    frames = [f.resize((GIF_WIDTH, height), Image.LANCZOS) for f in frames]
    # One palette for every frame, taken from the closed and the fully open
    # view together, so colours do not shimmer from frame to frame.
    sample = Image.new("RGB", (GIF_WIDTH, height * 2))
    sample.paste(frames[0], (0, 0))
    sample.paste(frames[len(frames) // 2], (0, height))
    palette = sample.quantize(colors=128, method=Image.MEDIANCUT, dither=Image.NONE)
    quantised = [f.quantize(palette=palette, dither=Image.NONE) for f in frames]
    quantised[0].save(path, save_all=True, append_images=quantised[1:], duration=GIF_FRAME_MS,
                      loop=0, optimize=True, disposal=1)


def render_all():
    """Write the stills and the pull-apart animation.  Returns the files written."""
    from PIL import Image
    from playwright.sync_api import sync_playwright

    for needed in ("index.html", "parts.json"):
        if not (VIEWER / needed).exists():
            raise FileNotFoundError(f"viewer/{needed} is missing; run build.py first")
    DOCS.mkdir(exist_ok=True)
    three_dir = os.environ.get("THREE_DIR")
    chromium = os.environ.get("CHROMIUM_PATH")

    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(_QuietHandler, directory=str(VIEWER)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    written = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                executable_path=chromium or None,
                args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"],  # software WebGL when headless
            )
            page = browser.new_page(viewport={"width": 1500, "height": 1100},
                                    device_scale_factor=2, color_scheme="light")
            if three_dir:
                for name, rel in THREE_FILES.items():
                    page.route(f"**/{name}", _serve_file(Path(three_dir) / rel))
            page.route("**/fonts.googleapis.com/**", lambda route, request: route.abort())  # only the 3D stage is captured

            page.goto(f"http://127.0.0.1:{server.server_address[1]}/")
            if not page.evaluate("!!(window.THREE && THREE.OrbitControls)"):
                raise RuntimeError("the viewer could not load three.js from its CDN; "
                                   "set THREE_DIR to a local copy of the three 0.128 package")
            page.wait_for_function("window.kitViewer && window.kitViewer.ready", timeout=60_000)
            page.evaluate("document.querySelector('.hint').hidden = true")
            stage = page.query_selector("#stage")

            for name, view, apart in STILLS:
                page.evaluate("([v, t]) => { kitViewer.explode(t); kitViewer.view(v); }", [view, apart])
                stage.screenshot(path=str(DOCS / name))
                written.append(DOCS / name)

            # Frame the camera on the fully open prop and hold it there, so
            # the parts move and the viewpoint does not.
            page.evaluate("() => { kitViewer.explode(1); kitViewer.view('quarter'); kitViewer.holdCamera(); }")
            frames = []
            for apart in _animation_steps():
                page.evaluate("t => kitViewer.explode(t)", apart)
                frames.append(Image.open(io.BytesIO(stage.screenshot())).convert("RGB"))
            browser.close()
        _write_gif(frames, DOCS / "pull-apart.gif")
        written.append(DOCS / "pull-apart.gif")
    finally:
        server.shutdown()
    return written


if __name__ == "__main__":
    for path in render_all():
        print(f"wrote {path.relative_to(HERE)}")
