# SolWind ad

A 27-second video in two cuts, made from real footage of the app.

| File | Use |
|---|---|
| `film/renders/solwind_ad_16x9.mp4` | YouTube, slides, LinkedIn |
| `film/renders/solwind_ad_9x16.mp4` | Reels, TikTok, Shorts (captions burned in) |
| `film/renders/solwind_ad.srt` | Subtitles for the 16:9 cut |

## Script

| Time | Picture | Voice |
|---|---|---|
| 0:00 | Map draws in | Every midnight, the grid has to guess tomorrow. |
| 0:04 | App: map plays a day | SolWind replays sun and wind, hour by hour, at three Philippine sites. |
| 0:10 | App: wind set to 0 MW | Change the plant, and every hour reruns. |
| 0:14 | App: 2026 audit | Its forecasts were tested on years they never saw. |
| 0:20 | −29% | Up to twenty-nine percent less error. |
| 0:23 | End card | SolWind. Read tomorrow's sky. |

Every number on screen comes from the app's result files: 170,856 site-hours; 71% → 37% renewables with no wind (Laoag); 17–29% lower error by site and year.

## Re-render

The app must be running on `localhost:8501`. `FFMPEG` must point to an ffmpeg with libx264.

```bash
cd marketing/film
../../.venv/bin/python record_clips.py map designer audit
python voice.py && python build_timeline.py          # pip install edge-tts
../../.venv/bin/python render.py video
../../.venv/bin/python render.py video --vertical --cap
../../.venv/bin/python mix.py && python finish.py
```

To use your own URL on the end card, add `?url=yourapp.streamlit.app` when you preview `solwind_film.html`, or edit `#url`.
