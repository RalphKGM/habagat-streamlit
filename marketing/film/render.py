"""Frame-exact render of habagat_film.html -> MP4 (video only; mix.py adds sound).

  render.py stills 1.5 10 14 ...       -> renders/still_<t>.png (quick visual checks)
  render.py video [--vertical] [--cap] -> renders/video_16x9.mp4 / video_9x16.mp4
"""
import asyncio, functools, http.server, os, subprocess, sys, threading
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
FFMPEG = os.environ.get("FFMPEG", "ffmpeg")


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
        def handle(self):
            try: super().handle()
            except (ConnectionResetError, BrokenPipeError): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=HERE))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv.server_address[1]


async def main(mode, args):
    vertical, cap = "--vertical" in args, "--cap" in args
    args = [a for a in args if not a.startswith("--")]
    W, H = (1080, 1920) if vertical else (1920, 1080)
    q = "capture" + ("&vertical" if vertical else "") + ("&cap" if cap else "")
    port = serve()
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome", args=["--autoplay-policy=no-user-gesture-required"])
        pg = await b.new_page(viewport={"width": W, "height": H})
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(f"http://127.0.0.1:{port}/habagat_film.html?{q}")
        await pg.evaluate("FILM.ready()"); await pg.wait_for_timeout(500)
        dur, fps = await pg.evaluate("[FILM.duration, FILM.fps]")
        os.makedirs(os.path.join(HERE, "renders"), exist_ok=True)
        if mode == "stills":
            for s in args:
                await pg.evaluate(f"FILM.renderAt({float(s)})")
                await pg.screenshot(path=os.path.join(HERE, "renders", f"still_{s}{'v' if vertical else ''}.png"))
        else:
            n = int(round(dur * fps))
            out = os.path.join(HERE, "renders", f"video_{'9x16' if vertical else '16x9'}{'_cap' if cap else ''}.mp4")
            ff = subprocess.Popen([FFMPEG, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg",
                                   "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                                   "-movflags", "+faststart", out], stdin=subprocess.PIPE)
            for i in range(n):
                await pg.evaluate(f"FILM.renderAt({i / fps})")
                ff.stdin.write(await pg.screenshot(type="jpeg", quality=94))
                if i % 150 == 0:
                    print(f"frame {i}/{n}", flush=True)
            ff.stdin.close(); ff.wait()
            print("wrote", out)
        if errs:
            print("page errors:", errs[:5])
        await b.close()

asyncio.run(main(sys.argv[1], sys.argv[2:]))
