# Habagat ad kit

Everything you need for the "advertisement" item on the final checklist:

1. **A finished 30-second ad**: `ad/habagat_ad.html` (open it in Chrome).
2. **Script, storyboard and voice-over** to record or narrate over it.
3. **Social copy** for posting.
4. **Research: tools that use Claude Code / Codex to make app ads**, with exact prompts to turn this into an MP4 with music and a voice-over.

---

## 1. The ready-made ad

`ad/habagat_ad.html` is a self-contained 30-second motion ad (1920×1080) in the app's own visual language. It uses the real Philippine outlines from the app, a monsoon wind-particle field, and real screenshots from `ad/shots/`. Keep `map_data.js` and `shots/` next to the HTML file.

| Key | Action |
|---|---|
| `F` | fullscreen |
| `H` | hide the help text |
| `R` | restart from 0 s |
| `Space` | pause / play |
| `←` `→` | seek 1 s |

- **Vertical 9:16 cut** (Reels, TikTok, Shorts): open `habagat_ad.html?vertical`.
- **Your deployed URL** on the end card: `habagat_ad.html?url=yourname.streamlit.app`.
- **Jump to a moment:** `habagat_ad.html?t=18`.

**Export to MP4 (simplest):** open in Chrome → `F` → `H` → `R` → record the screen.
- **macOS:** `Cmd+Shift+5` → *Record Entire Screen*, stop after the end card (about 30 s).
- **Windows:** Xbox Game Bar (`Win+G`) or OBS.

Trim the start and end in QuickTime or Clipchamp, then add the voice-over and music below in CapCut, iMovie, or Canva.

**Export to MP4 (frame-perfect, with AI):** see section 4.

## 2. Script and storyboard (30 s)

| Time | Picture | On-screen text | Voice-over (calm, matter-of-fact) |
|---|---|---|---|
| 0.0–4.6 | Dark screen, the Philippine coastline draws itself in, monsoon wind particles drift | *Every midnight, the grid has to guess tomorrow.* | "Every night, the people who run our grid have to guess tomorrow." |
| 4.6–9.2 | Luzon, Visayas and Mindanao fill in one by one, and the three sites light up | *How much sun. How much wind. Hour by hour, at three sites across the Philippines.* | "How much sun, and how much wind, hour by hour?" |
| 9.2–13.4 | The wind glyph draws in, then the wordmark | *Habagat · Solar-wind forecasting for Philippine microgrids* | "Meet Habagat." |
| 13.4–17.8 | Map screenshot with a hover card, stat counts up | *Hover any island group · 131,544 hourly weather records* | "It replays five years of NASA weather at Laoag, Mactan and General Santos." |
| 17.8–22.2 | Forecast accuracy screenshot, stat counts up | *Tested on a year it never saw · −27% error (up to)* | "Its forecasts were tested on a year they'd never seen, with up to 27% less error." |
| 22.2–26.4 | Grid planning screenshot, stat counts up | *Better forecasts, steadier plans · −24% adjustment (up to)* | "Better forecasts mean steadier grid plans." |
| 26.4–30.4 | End card over a faded map, with the URL | *Habagat · habagat.streamlit.app* | "Habagat." |

**Music:** warm, minimal piano or marimba with a soft pulse, building at 9 s (logo) and resolving at 26.4 s. Use royalty-free tracks from the YouTube Audio Library, Pixabay Music, or an AI generator such as ElevenLabs Music or Google Lyria. Keep music about 12 dB under the voice.

**Claims check:** every number in the ad comes from the app's own result files.
- **27%:** XGBoost vs. the best baseline at Laoag. The range across sites is 17–27%, so "up to 27%" is accurate.
- **24%:** the grid-plan adjustment at Mactan. The range is 18–24%.
- **131,544:** hourly weather records across 2020–2024.

Avoid saying "saves money" or "prevents blackouts". The study doesn't measure either.

## 3. Social copy

**LinkedIn / Facebook**
> Every midnight, grid operators have to guess tomorrow's sun and wind. For our CSS142 project we built **Habagat**, which simulates a solar-wind microgrid at Laoag, Mactan and General Santos from five years of NASA POWER weather. It tests machine-learning day-ahead forecasts on a held-out 2025. XGBoost cut forecast error by up to 27% and grid-plan adjustments by up to 24% compared with simple baselines. Try it: https://habagat.streamlit.app · Code: https://github.com/<you>/habagat
> #RenewableEnergy #MachineLearning #Philippines #Streamlit #DataScience

**X / Threads (≤280 chars)**
> Every midnight the grid has to guess tomorrow's sun & wind. Habagat replays 5 years of NASA weather at 3 PH sites and tests ML forecasts on a year they never saw: up to 27% less error. ☀️🌬️ https://habagat.streamlit.app

**TikTok / Reels caption (vertical cut)**
> POV: you taught a model to read tomorrow's sky ☀️🌬️🔋 #habagat #renewables #machinelearning #studentproject

---

## 4. Research: making app ads with Claude Code or Codex

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
- **Give the agent one strong reference.** For you, that's `habagat_ad.html`.
- **Hand it the real value proposition.** Point it at the README and the results.
- **Use each model for what it's best at.**

One kit that came up in search (video-shotcraft) returned a 404 when checked, so it's not listed.

### Recommended path for Habagat

**Option A: zero setup (10 minutes).** Screen-record `habagat_ad.html` (section 1). Add the voice-over with free TTS or your own voice, plus music. This is good enough for the checklist.

**Option B: frame-perfect MP4 with HyperFrames (about 30 minutes).** Install Node.js 22+ and FFmpeg (`brew install node ffmpeg`), then in this folder:

```bash
claude plugin install hyperframes@hyperframes      # or: npx skills add heygen-com/hyperframes --full-depth --yes
claude
```

Paste this prompt:

```text
Use the HyperFrames skill to turn marketing/ad/habagat_ad.html into a HyperFrames composition
and render it to marketing/ad/renders/habagat_30s_16x9.mp4 (1920x1080, 30 fps) and
habagat_30s_9x16.mp4 (1080x1920).
Keep the exact scene timings, copy, colours (#0F1215 background, #E6E9EB text, #F2B544 solar, #5BB5E0 wind, #7FD3A8 accent),
fonts (IBM Plex Sans, IBM Plex Mono), map_data.js and the screenshots in marketing/ad/shots/.
Remove the keyboard HUD. Do not invent new numbers; every statistic must come from the HTML.
Show me a preview before the final render.
```

**Option C: Remotion, with voice-over and captions.** Run `npx skills add remotion-dev/skills`, plus `claude-promo-video` or `promo-video-skill` if you want an AI voice. Then prompt:

```text
Make a 30-second promo video for this app (Habagat) for a university final defense and social media.
Follow the storyboard and voice-over in marketing/README.md section 2 exactly, and use
marketing/ad/habagat_ad.html as the visual reference. Use the real screenshots in marketing/ad/shots/,
the brand colours in .streamlit/config.toml, and only the statistics already in the README.
Render 16:9 and 9:16 MP4s to marketing/ad/renders/.
```

**Codex users:** the Remotion skills and HyperFrames both list Codex as supported. Run the same prompts in Codex CLI from this folder.

### Tips that make AI-made ads look less generic

- Feed the agent **your** brand tokens and real screenshots. Never let it invent UI.
- Ask for **one idea per scene** and on-screen text of 7 words or fewer.
- Ask it to **review its own render** frame by frame at each scene boundary before it calls the video done.
- Lock every claim to a source file, and tell the agent not to round up.
