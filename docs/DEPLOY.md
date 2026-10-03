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
  1. **Overview**: the hero, the four numbers, the pipeline.
  2. **Live plant**: press *Windiest* at Laoag and point out the rotor, battery and flows.
  3. **System designer**: drag wind to 0 and watch coverage drop. Then show the fingerprint heatmap.
  4. **Forecast lab**: the leaderboard. Then *Play day* with the reference hidden, and reveal it.
  5. **Grid planning**: the replay on 15 Jul 2025, comparing XGBoost with Previous day.
  6. **Methods**: mention that the test suite reproduces the paper's tables exactly.

## Rebuilding the data

If the research outputs change, regenerate `data/` from the full project and rerun the tests:

```bash
python scripts/build_data.py ~/Downloads/Solar_Wind_Classroom_Presentation
python -m pytest tests -q
```
