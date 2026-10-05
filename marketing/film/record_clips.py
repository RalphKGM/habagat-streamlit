"""Record real, high-resolution clips of the running app (localhost:8501) for the ad.

Uses Chrome DevTools screencast (JPEG frames + timestamps), then ffmpeg turns each clip
into a constant 30 fps, all-keyframe MP4 so the film page can seek it frame-exactly.
Run with the app's venv:  ../../.venv/bin/python record_clips.py [clip ...]
"""
import asyncio, base64, os, shutil, subprocess, sys
from playwright.async_api import async_playwright

URL = "http://localhost:8501"
HERE = os.path.dirname(os.path.abspath(__file__))
FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
W, H, DSF = 1280, 720, 1.5          # 1920×1080 pixels


class Recorder:
    def __init__(self, page, name):
        self.page, self.name, self.frames = page, name, []
        self.dir = os.path.join(HERE, "frames", name)

    async def start(self):
        shutil.rmtree(self.dir, ignore_errors=True); os.makedirs(self.dir)
        self.cdp = await self.page.context.new_cdp_session(self.page)
        self.cdp.on("Page.screencastFrame", lambda f: asyncio.ensure_future(self._frame(f)))
        await self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92,
                                                      "maxWidth": int(W * DSF), "maxHeight": int(H * DSF)})

    async def _frame(self, f):
        path = os.path.join(self.dir, f"{len(self.frames):05d}.jpg")
        with open(path, "wb") as fh:
            fh.write(base64.b64decode(f["data"]))
        self.frames.append((path, f["metadata"]["timestamp"]))
        try:
            await self.cdp.send("Page.screencastFrameAck", {"sessionId": f["sessionId"]})
        except Exception:
            pass

    async def stop(self):
        await self.page.wait_for_timeout(300)
        await self.cdp.send("Page.stopScreencast")
        await self.page.wait_for_timeout(300)
        lst = os.path.join(self.dir, "list.txt")
        with open(lst, "w") as fh:
            for (p, t), nxt in zip(self.frames, self.frames[1:] + [(None, self.frames[-1][1] + 1 / 30)]):
                fh.write(f"file '{p}'\nduration {max(nxt[1] - t, 0.001):.4f}\n")
            fh.write(f"file '{self.frames[-1][0]}'\n")
        os.makedirs(os.path.join(HERE, "clips"), exist_ok=True)
        out = os.path.join(HERE, "clips", f"{self.name}.mp4")
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                        "-vf", "fps=30,scale=1920:1080:flags=lanczos,format=yuv420p",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-g", "1", out], check=True)
        dur = self.frames[-1][1] - self.frames[0][1]
        print(f"{self.name}: {len(self.frames)} frames over {dur:.1f}s -> {out}")


async def settle(pg, extra=1500):
    await pg.wait_for_selector('[data-testid="stMainBlockContainer"]', timeout=60000)
    await pg.wait_for_function("!document.querySelector('[data-testid=\"stStatusWidget\"]')", timeout=90000)
    await pg.wait_for_timeout(extra)


async def glide(pg, x0, y0, x1, y1, ms=700, steps=30):
    """Ease-in-out mouse move so the cursor reads as a person, not a teleport."""
    for i in range(1, steps + 1):
        u = i / steps; e = u * u * (3 - 2 * u)
        await pg.mouse.move(x0 + (x1 - x0) * e, y0 + (y1 - y0) * e)
        await pg.wait_for_timeout(ms / steps)


CURSOR_JS = """
(() => { if (window.__cur) return; const c = document.createElement('div'); window.__cur = c;
  c.style.cssText = 'position:fixed;z-index:2147483647;left:0;top:0;width:22px;height:22px;pointer-events:none;'
   + 'transform:translate(-3px,-2px);transition:transform .08s';
  c.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22"><path d="M3 2l7 19 2.6-7.4L20 11z" fill="#15191C" stroke="#FFFFFF" stroke-width="1.6" stroke-linejoin="round"/></svg>';
  document.documentElement.appendChild(c);
  addEventListener('mousemove', e => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; }, true);
  addEventListener('mousedown', () => c.style.transform = 'translate(-3px,-2px) scale(.82)', true);
  addEventListener('mouseup', () => c.style.transform = 'translate(-3px,-2px)', true);
})();
"""


async def cursor(pg):
    # Synthetic cursor on the main page; iframes forward nothing, so we also mirror moves from Python.
    await pg.evaluate(CURSOR_JS)


async def move(pg, x0, y0, x1, y1, ms=700):
    for i in range(1, 31):
        u = i / 30; e = u * u * (3 - 2 * u); x = x0 + (x1 - x0) * e; y = y0 + (y1 - y0) * e
        await pg.mouse.move(x, y)
        await pg.evaluate(f"window.__cur && (window.__cur.style.left='{x}px', window.__cur.style.top='{y}px')")
        await pg.wait_for_timeout(ms / 30)
    return x1, y1


async def map_clip(pg):
    await pg.goto(URL + "/"); await settle(pg, 4000); await cursor(pg)
    r = Recorder(pg, "map"); await r.start()
    p = await move(pg, 1000, 600, 560, 300, 900)            # over Luzon
    await pg.wait_for_timeout(900)
    p = await move(pg, *p, 538, 392, 700)                   # Mactan
    await pg.wait_for_timeout(500)
    await pg.mouse.click(538, 392); await pg.wait_for_timeout(1400)
    p = await move(pg, *p, 845, 668, 900)                   # PLAY
    await pg.mouse.down(); await pg.wait_for_timeout(90); await pg.mouse.up()
    await pg.wait_for_timeout(500)
    await move(pg, *p, 700, 520, 800)
    await pg.wait_for_timeout(4200)
    await r.stop()


async def picker_clip(pg):
    await pg.goto(URL + "/"); await settle(pg, 4000); await cursor(pg)
    fr = [f for f in pg.frames if "map" in f.url.split("?")[0] and "component" in f.url][0]
    box = await (await fr.query_selector(".dp-label")).bounding_box()
    r = Recorder(pg, "picker"); await r.start()
    p = await move(pg, 600, 400, box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, 900)
    await pg.mouse.click(*p); await pg.wait_for_timeout(900)
    await fr.select_option(".dp-yr", "2026"); await pg.wait_for_timeout(700)
    await fr.select_option(".dp-mon", "4"); await pg.wait_for_timeout(700)
    day = await (await fr.query_selector(".dp-day[data-d='2026-05-20']")).bounding_box()
    p = await move(pg, *p, day["x"] + day["width"] / 2, day["y"] + day["height"] / 2, 800)
    await pg.wait_for_timeout(250); await pg.mouse.click(*p)
    await pg.wait_for_timeout(3600)
    await move(pg, *p, 845, 668, 800); await pg.mouse.click(845, 668)
    await pg.wait_for_timeout(3500)
    await r.stop()


async def designer_clip(pg):
    await pg.goto(URL + "/designer"); await settle(pg, 2500); await cursor(pg)
    thumb = pg.locator('[data-testid="stSlider"]').nth(1).locator('[role="slider"]')
    b = await thumb.bounding_box(); x, y = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
    track = await pg.locator('[data-testid="stSlider"]').nth(1).bounding_box()
    r = Recorder(pg, "designer"); await r.start()
    await pg.mouse.move(260, 640)
    p = await move(pg, 260, 640, x, y, 900)
    await pg.mouse.down()
    p = await move(pg, *p, track["x"] + 2, y, 1100)          # wind → 0 MW
    await pg.mouse.up(); await pg.wait_for_timeout(3200)
    await pg.mouse.down()
    p = await move(pg, *p, track["x"] + track["width"] * 2 / 3, y, 1200)   # wind → 2 MW
    await pg.mouse.up(); await move(pg, *p, 300, 640, 600); await pg.wait_for_timeout(5000)
    await r.stop()


async def rolling_clip(pg):
    await pg.goto(URL + "/rolling"); await settle(pg, 2500); await cursor(pg)
    r = Recorder(pg, "rolling"); await r.start()
    p = await move(pg, 900, 600, 880, 255, 900)              # the 2024 test cell
    await pg.wait_for_timeout(500)
    p = await move(pg, *p, 1140, 366, 1100)                  # 2026 Jan–Jun
    await pg.wait_for_timeout(700)
    for _ in range(14):
        await pg.mouse.wheel(0, 70); await pg.wait_for_timeout(45)
    await pg.wait_for_timeout(2600)
    await r.stop()


async def calendar_clip(pg):
    await pg.goto(URL + "/rolling"); await settle(pg, 2500); await cursor(pg)
    cal = pg.locator(".js-plotly-plot").nth(3)
    await cal.scroll_into_view_if_needed(); await pg.mouse.move(640, 360); await pg.mouse.wheel(0, -120)
    await pg.wait_for_timeout(1500)
    pts = cal.locator(".scatterlayer .point")
    r = Recorder(pg, "calendar"); await r.start()
    pt = await pts.nth(200).bounding_box()
    p = await move(pg, 640, 650, pt["x"] + pt["width"] / 2, pt["y"] + pt["height"] / 2, 1100)
    await pg.wait_for_timeout(700)
    await pg.mouse.click(*p); await pg.wait_for_timeout(2400)
    for _ in range(10):
        await pg.mouse.wheel(0, 60); await pg.wait_for_timeout(45)
    await pg.wait_for_timeout(2600)
    await r.stop()


async def planning_clip(pg):
    await pg.goto(URL + "/planning"); await settle(pg, 2500); await cursor(pg)
    r = Recorder(pg, "planning"); await r.start()
    p = await move(pg, 900, 600, 520, 320, 900)
    await pg.wait_for_timeout(1000)
    await pg.mouse.move(640, 400)
    for _ in range(16):
        await pg.mouse.wheel(0, 60); await pg.wait_for_timeout(45)
    await pg.wait_for_timeout(6500)
    await r.stop()


async def audit_clip(pg):
    await pg.goto(URL + "/audit"); await settle(pg, 3000); await cursor(pg)
    r = Recorder(pg, "audit"); await r.start()
    p = await move(pg, 900, 600, 200, 200, 700)
    for x in (200, 420, 640, 860, 1080):               # walk the five steps
        p = await move(pg, *p, x, 200, 380)
        await pg.wait_for_timeout(200)
    for _ in range(9):
        await pg.mouse.wheel(0, 50); await pg.wait_for_timeout(40)
    await pg.wait_for_timeout(600)
    p = await move(pg, *p, 300, 430, 600)
    p = await move(pg, *p, 1000, 430, 2400)             # sweep along the 2026 daily chart
    await pg.wait_for_timeout(800)
    await r.stop()


CLIPS = dict(audit=audit_clip, map=map_clip, picker=picker_clip, designer=designer_clip, rolling=rolling_clip,
             calendar=calendar_clip, planning=planning_clip)


async def main(names):
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome")
        ctx = await b.new_context(viewport={"width": W, "height": H}, device_scale_factor=DSF)
        for n in names:
            pg = await ctx.new_page()
            await CLIPS[n](pg)
            await pg.close()
        await b.close()

asyncio.run(main(sys.argv[1:] or list(CLIPS)))
