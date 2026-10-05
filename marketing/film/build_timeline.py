"""Fit scene lengths to the voice lines -> timeline.json / timeline.js (captions keep the written text)."""
import json, re

PLAN = [  # scene, minimum length (s), voice delay into the scene (s)
    ("hook", 3.6, .3), ("map", 6.2, .3), ("designer", 4.4, .3),
    ("audit", 5.2, .3), ("stat", 3.6, .3), ("end", 4.2, .5),
]
vo = {v["key"]: v for v in json.load(open("audio/vo.json"))}
norm = lambda x: re.sub(r"[^\w]", "", x).lower()
t, scenes = 0.0, []
for sid, length, delay in PLAN:
    v = vo[sid]; length = max(length, delay + v["dur"] + .4); start = t + delay
    words, wi = [], 0
    for tok in v["text"].split():  # caption tokens timed from the TTS word boundaries
        hit = next((j for j in range(wi, min(wi + 3, len(v["words"]))) if norm(v["words"][j]["w"])[:3] == norm(tok)[:3]), None)
        if hit is not None:
            words.append({"w": tok, "t": round(start + v["words"][hit]["t"], 3)}); wi = hit + 1
        else:
            words.append({"w": tok, "t": round((words[-1]["t"] if words else start) + .3, 3)})
    scenes.append({"id": sid, "from": round(t, 3), "to": round(t + length, 3), "vo": sid, "voAt": round(start, 3),
                   "voDur": v["dur"], "words": words})
    t += length
tl = {"fps": 30, "duration": round(t, 3), "scenes": scenes}
json.dump(tl, open("timeline.json", "w"), indent=1)
open("timeline.js", "w").write("window.TL = " + json.dumps(tl) + ";\n")
for s in scenes:
    print(f"{s['id']:9s} {s['from']:5.2f}–{s['to']:5.2f}  " + " ".join(w["w"] for w in s["words"]))
print("total", tl["duration"])
