# SolWind ad kit

1. **The finished 60-second ad** (`film/renders/`): 16:9 and 9:16 MP4s, with voice-over, an original soundtrack, captions and subtitles.
2. **The source** to change it and re-render (`film/`).
3. **Script, claims check and social copy** (below).
4. **Research** on tools that make app ads with Claude Code or Codex.

The older 30-second motion piece is still in `ad/solwind_ad.html`.

---

## 1. The film

| File | Use |
|---|---|
| `film/renders/solwind_ad_16x9.mp4` | YouTube, presentations, LinkedIn (1920×1080, 30 fps, about 59 s) |
| `film/renders/solwind_ad_9x16.mp4` | Reels, TikTok, Shorts (1080×1920, captions burned in) |
| `film/renders/solwind_ad.srt` | Subtitles for the 16:9 upload |
| `film/renders/thumb_end.png`, `thumb_result.png` | Thumbnails |
| `film/renders/solwind_teaser.gif` | 6-second silent teaser for READMEs and chats |

### How it was made (all free, all local)

| Step | Tool | File |
|---|---|---|
| Real product footage | Playwright drives the running app; Chrome DevTools screencast captures 1920×1080 frames with a visible cursor | `film/record_clips.py` → `film/clips/*.mp4` |
| Voice-over | Microsoft Edge neural TTS (`edge-tts`, voice *en-US-AndrewNeural*), with word timings | `film/voice.py` → `film/audio/` |
| Timeline | Scene lengths are fitted to the voice lines | `film/timeline.json` |
| Motion design | One HTML page where every frame is a pure function of time: map outlines, monsoon wind particles, the fold grid, result bars, and the app clips seeked frame by frame | `film/solwind_film.html` |
| Frame-exact render | Headless Chrome steps 30 fps and pipes frames to ffmpeg (H.264) | `film/render.py` |
| Music | Synthesised in numpy (pad, marimba pulse, wind noise, riser), ducked under the voice, loudness-normalised to −15 LUFS | `film/mix.py` |
| Finish | Mux, subtitles, thumbnails, GIF | `film/finish.py` |

### Re-render after a change

The app must be running on `localhost:8501` for step 1. `FFMPEG` points to any ffmpeg with libx264 (`brew install ffmpeg`, or `pip install imageio-ffmpeg`).

```bash
cd marketing/film
../../.venv/bin/python record_clips.py          # optional: re-shoot the app clips
python voice.py                                  # needs: pip install edge-tts
# rebuild timeline.json if the voice lines changed (see the scene plan at the top of this README)
../../.venv/bin/python render.py video                     # 16:9
../../.venv/bin/python render.py video --vertical --cap    # 9:16 with captions
../../.venv/bin/python mix.py && python finish.py
```

Preview without rendering: run `python3 -m http.server` in `film/` and open `solwind_film.html` (Space to pause, arrows to seek, `?vertical&cap` for the vertical cut).

- **Deployed URL on the end card:** add `?url=yourname.streamlit.app` to the page, or edit `#url` in the HTML, then re-render.

## 2. Script (about 59 s)

| Time | Picture | Voice-over |
|---|---|---|
| 0:00 | Coastline draws in, monsoon wind particles | "Every midnight, the grid has to guess tomorrow." |
| 0:04 | Luzon, Visayas and Mindanao fill in, and the three sites light up | "How much sun? How much wind? Hour by hour." |
| 0:09 | Logo | "This is SolWind." |
| 0:12 | **App:** map hover, switch to Mactan, press PLAY, with 170,856 counting up | "It replays six and a half years of NASA weather, hour by hour, at three sites across the Philippines." |
| 0:20 | **App:** day picker, jump to 20 May 2026 | "Pick any day, right up to June 2026, and watch it play out." |
| 0:26 | **App:** System designer, wind to 0 MW (renewables fall from 71.2% to 37.0%) | "Change the plant, and every hour reruns. Take the wind away, and the grid has to cover it." |
| 0:32 | Fold grid builds on each spoken year | "Then the forecasts face a year they've never seen. 2024. 2025. And 2026." |
| 0:41 | **App:** Rolling test calendar, open one day | "Every day is forecast automatically, at midnight." |
| 0:45 | Result bars for each site and year | "Seventeen to twenty-nine percent less error than the best baseline." |
| 0:50 | **App:** grid-plan day replay, with 16–25% | "And grid plans that need up to a quarter less correction." |
| 0:54 | End card | "SolWind. Read tomorrow's sky." |

**Claims check.** Every number comes from the app's result files.
- **170,856:** site-hours of NASA POWER weather, January 2020 to June 2026 (56,952 per site).
- **17–29%:** XGBoost combined MAE against the better baseline, per site and test year (`data/rolling/rolling_metrics.csv`, `available_test`).

  | Site | 2024 | 2025 | 2026 H1 |
  |---|---|---|---|
  | Laoag | 23.8% | 26.9% | 29.2% |
  | Mactan | 17.6% | 25.7% | 26.6% |
  | General Santos | 22.8% | 17.2% | 17.5% |

- **16–25% ("up to a quarter"):** grid-plan adjustment against the best baseline, every site and test year.
- **71.2% → 37.0%:** Laoag demand met by renewables, standard design vs. 0 MW wind, read off the designer during the shoot.

Don't add "saves money" or "prevents blackouts". The study doesn't measure either. The end card says "Modeled output, not metered plant data".

## 3. Social copy

**LinkedIn / Facebook**
> Every midnight, grid operators have to guess tomorrow's sun and wind. **SolWind** replays six and a half years of NASA POWER weather, hour by hour, for a 1 MW solar + 1 MW wind + 2 MWh battery system at Laoag, Mactan and General Santos. Then it tests day-ahead forecasts on years the model never saw: 2024, 2025 and early 2026. XGBoost had 17–29% less error than the best simple baseline at every site in every year, and its grid plans needed 16–25% less correction.
> Code: https://github.com/RalphKGM/habagat-streamlit
> #RenewableEnergy #MachineLearning #Philippines #Streamlit #DataScience

**X / Threads (≤280 chars)**
> Every midnight the grid has to guess tomorrow's sun & wind. SolWind replays 6.5 years of NASA weather at 3 PH sites and tests forecasts on years they never saw: 17–29% less error than the best baseline. ☀️🌬️ github.com/RalphKGM/habagat-streamlit

**Reels / TikTok / Shorts caption (vertical cut)**
> Read tomorrow's sky ☀️🌬️🔋 Day-ahead solar + wind forecasts for three Philippine sites, tested on years the model never saw. #solwind #renewables #machinelearning #philippines

---

## 4. Research: making app ads with Claude Code or Codex

The film in section 1 follows the code-based approach described here. It uses plain HTML, Playwright and ffmpeg instead of Remotion or HyperFrames, so it needs no extra install.

As of October 2026, the common approach is **code-based video**. The AI agent doesn't generate pixels the way Sora or Veo do. It writes a video as code (React with Remotion, or HTML/CSS/GSAP with HyperFrames) and a renderer turns that code into a frame-perfect MP4. That keeps your real UI, fonts, colors and numbers exact, which text-to-video models can't guarantee.

### Tools worth knowing

| Tool | What it is | Works with | Needs | Licence |
|---|---|---|---|---|
| **[Remotion Agent Skills](https://www.remotion.dev/docs/ai/skills)** (`npx skills add remotion-dev/skills`) | Official skills that teach coding agents Remotion's timing, media, captions and render rules. The foundation most other kits build on. | Claude Code, Codex, Cursor | Node.js | Remotion licence: free for individuals and small teams |
| **[HeyGen HyperFrames](https://github.com/heygen-com/hyperframes)** (`claude plugin install hyperframes@hyperframes`, or `npx hyperframes init`) | Open-source HTML-to-MP4 renderer built for agents. Scenes are plain HTML with `data-*` timing and GSAP/CSS animation. Deterministic headless-Chrome render. **Closest fit for this ad, which is already HTML/CSS.** | Claude Code, Codex, Cursor | Node.js 22+, FFmpeg | Apache-2.0 |
| **[EveryInc/product-launch-video](https://github.com/EveryInc/product-launch-video)** | Claude Code skill + Remotion scaffold for 15–30 s launch videos. Workflow: brand tokens → storyboard → scenes → render, followed by four parallel AI "reviewers". Outputs a 1080p MP4, a GIF and social captions. | Claude Code | Node 18+, ffmpeg (GIF) | MIT |
| **[claude-promo-video](https://github.com/Iliesseu28/claude-promo-video)** | Claude Code plugin: storyboard, animated cursor with zooms and clicks over your real screens, Gemini TTS voice-over, and Whisper word-synced subtitles. | Claude Code | Node 20+, ffmpeg, Python, Whisper, Gemini API key | MIT |
| **[AKCodez/promo-video-skill](https://github.com/AKCodez/promo-video-skill)** | Scans a repo for branding, then builds 30/60/90 s promos in landscape **and** portrait, with ElevenLabs voice-over and music. | Claude Code | Node 18+, ElevenLabs key (free tier) | MIT |

**Real-world example:** [Po-Shen Loh's weekend ad campaign for about $100](https://poshenloh.com/posts/20260904-ai-video-ad-campaign).
- Claude Code designed the compositions and music direction in Remotion.
- Codex handled image work (blurring student names).
- Google Lyria and ElevenLabs Music produced the soundtracks.

His lessons apply directly here:
- **Give the agent one strong reference.** For you, that's `solwind_ad.html`.
- **Hand it the real value proposition.** Point it at the README and the results.
- **Use each model for what it's best at.**

One kit that came up in search (video-shotcraft) returned a 404 when checked, so it's not listed.

### If you want to go further

- **HyperFrames or Remotion:** port `film/solwind_film.html` to either one to get timeline editing in a GUI.
- **Better voice:** the free tiers of ElevenLabs have more natural voices. Swap the files in `film/audio/`, rebuild `timeline.json`, then re-render.
- **Licensed music:** replace the synthesised bed in `mix.py` with a track from the YouTube Audio Library or Pixabay Music. Keep it about 12 dB under the voice.

### Tips that make AI-made ads look less generic

- Feed the agent **your** brand tokens and real screenshots. Never let it invent UI.
- Ask for **one idea per scene** and on-screen text of 7 words or fewer.
- Ask it to **review its own render** frame by frame at each scene boundary before it calls the video done.
- Lock every claim to a source file, and tell the agent not to round up.
