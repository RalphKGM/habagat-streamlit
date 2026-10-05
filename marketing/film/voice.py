"""SolWind ad voice-over lines -> audio/vo_XX.mp3 + audio/vo.json (durations and word timings) via edge-tts (free)."""
import asyncio, json, os, subprocess, sys
import edge_tts

VOICE = os.environ.get("VOICE", "en-US-AndrewNeural")
LINES = [
    ("hook",     "Every midnight, the grid has to guess tomorrow."),
    ("map",      "SolWind replays sun and wind, hour by hour, at three Philippine sites."),
    ("designer", "Change the plant, and every hour reruns."),
    ("audit",    "Its forecasts were tested on years they never saw."),
    ("stat",     "Up to twenty-nine percent less error."),
    ("end",      "SolWind. Read tomorrow's sky."),
]
SAY = {"SolWind": "Sol Wind"}  # spoken form; captions keep the written name
FFPROBE_FREE = os.environ.get("FFMPEG", "ffmpeg")


async def one(key, text):
    out = f"audio/vo_{key}.mp3"
    spoken = text
    for written, said in SAY.items():
        spoken = spoken.replace(written, said)
    com = edge_tts.Communicate(spoken, VOICE, rate="+2%", boundary="WordBoundary")
    words = []
    with open(out, "wb") as fh:
        async for c in com.stream():
            if c["type"] == "audio":
                fh.write(c["data"])
            elif c["type"] == "WordBoundary":
                words.append({"w": c["text"], "t": c["offset"] / 1e7, "d": c["duration"] / 1e7})
    # exact decoded duration
    r = subprocess.run([FFPROBE_FREE, "-i", out, "-f", "null", "-"], capture_output=True, text=True)
    t = [l for l in r.stderr.split("\n") if "time=" in l][-1].split("time=")[1].split()[0]
    h, m, s = t.split(":"); dur = int(h) * 3600 + int(m) * 60 + float(s)
    return {"key": key, "text": text, "file": out, "dur": round(dur, 3), "words": words}


async def main():
    os.makedirs("audio", exist_ok=True)
    res = [await one(k, t) for k, t in LINES]
    json.dump(res, open("audio/vo.json", "w"), indent=1)
    for r in res:
        print(f"{r['key']:9s} {r['dur']:5.2f}s  {len(r['words'])} words")
    print("total", round(sum(r["dur"] for r in res), 2))

asyncio.run(main())
