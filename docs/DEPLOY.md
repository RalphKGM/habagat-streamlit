# Deploy Habagat

## 1. Push to GitHub

From this folder:

```bash
git init
git add .
git commit -m "Habagat: solar-wind forecasting app"
git branch -M main
git remote add origin https://github.com/<your-username>/habagat.git
git push -u origin main
```

Create the empty repository on github.com first (no README, so the push doesn't conflict). `.gitignore` already excludes `.venv/`, caches and macOS files. The whole repo is about 10 MB. The largest file is 2.3 MB, well under GitHub's 100 MB limit.

## 2. Deploy on Streamlit Community Cloud (free)

1. Go to **share.streamlit.io** and sign in with GitHub.
2. Click **Create app → Deploy a public app from GitHub**.
3. Repository: `<your-username>/habagat` · Branch: `main` · Main file path: `streamlit_app.py`.
4. **App URL**: choose `habagat` (giving `habagat.streamlit.app`) if it's free. Otherwise pick another name and update the URL in the ad: `marketing/ad/habagat_ad.html?url=yourname.streamlit.app`.
5. **Advanced settings → Python version**: 3.11 or 3.12.
6. Deploy. The first build takes 2–4 minutes. The first page load runs the physics once (about 2 seconds), and after that it's cached.

No secrets or API keys are needed.

## 3. Before the defense

- Open the deployed URL once beforehand to wake the app. Free apps sleep after a period of inactivity.
- Keep the local launcher (`Run Habagat.command`) as an offline fallback.
- Suggested demo path (about 3 minutes):
  1. **Map**: hover the three regions, click Laoag, then press play on the timeline and watch the colors and wind shift through the day. Switch the legend to *Capacity factor*, then open the *Forecast 2025* tab in the panel.
  2. **Live plant**: press *Windiest* and point out the rotor, battery and flows.
  3. **System designer**: drag wind to 0 and watch renewable coverage drop. Then show the surplus heatmap.
  4. **Forecast accuracy**: the leaderboard, then *Play day* with the reference hidden, then reveal it.
  5. **Grid planning**: the replay on 15 Jul 2025, comparing XGBoost with Previous day.
  6. **Rolling test**: point at the fold grid (fit, select, test), then click a red and a green day in the calendar.
  7. **Methodology**: the comparison with related studies; mention that the test suite reproduces the paper's tables exactly.

## Rebuilding the data

If the research outputs change, regenerate `data/` from the full project and rerun the tests:

```bash
python scripts/build_data.py ~/Downloads/Solar_Wind_Classroom_Presentation
python scripts/extend_weather.py "~/Desktop/final-submission-simulation/[3 - STREAMLIT]/project"
python scripts/build_rolling.py "~/Desktop/final-submission-simulation/[3 - STREAMLIT]/project"
python -m pytest tests -q
```
