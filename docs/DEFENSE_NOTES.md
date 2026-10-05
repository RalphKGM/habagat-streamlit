# Defense notes

These notes are for presenting. Every number below comes from `data/rolling/` or the paper's tables.

## 30-second pitch

> Every night, grid operators guess how much sun and wind tomorrow will bring. We built SolWind. It simulates the same 1 MW solar + 1 MW wind system with a 2 MWh battery at Laoag, Mactan and General Santos, using hourly NASA POWER weather. Then it tests day-ahead forecasts year by year: 2024, 2025 and January–June 2026, each predicted by a model that only saw earlier years. XGBoost beat both simple baselines at every site in every test year. It had 17–29% lower error, and the grid plans built from it needed 16–25% less correction.

## Headline numbers

| | Laoag | Mactan | General Santos |
|---|---|---|---|
| Mean annual energy, 2020–2024 | 3,563 MWh | 2,751 MWh | 1,866 MWh |
| XGBoost combined MAE 2024 / 2025 / 2026 H1 (MW) | 0.109 / 0.122 / 0.095 | 0.083 / 0.086 / 0.084 | 0.064 / 0.060 / 0.053 |
| Lower error vs best baseline, each year | 24–29% | 18–27% | 17–23% |
| Less grid-plan adjustment vs best baseline, each year | 16–18% | 17–25% | 18–23% |

- 131,544 site-hours of physics, 2020–2024.
- 2026 stops at 30 June: NASA POWER irradiance was not released for later months when the test was run.
- All 2026 paired bootstrap intervals (7-day blocks, 2,000 resamples) favour XGBoost.
- Dropping 2020 from training (the recent window) helps Laoag and General Santos slightly and hurts Mactan. A shorter window is not reliably better.

## Demo path (about 4 minutes)

1. **Map**: hover the three island groups, click Laoag and press PLAY.
2. **System designer**: drag wind to 0 and watch coverage fall.
3. **Rolling test**: walk through the fold grid (fit, select, test). Then click one green and one red day in the calendar. This answers "do you have to click day by day?": every day is forecast automatically at midnight.
4. **2026 forecast**: show the five steps (fit 2020–2024, select on 2025, refit 2020–2025, forecast 2026 at midnight, score once). Then switch to "Each hour" to show computed vs forecast, and point at "Largest difference 9.9e-07 MW": the app reruns the physics and gets the same 2026 values the forecasts were scored against.
5. **Grid planning**: replay a day. The plan is fixed at midnight and reality fills in.
6. **Methodology**: the related-work table, then the limitations.

## How we compare with related work (one slide)

- **Forecasting papers** (Hu 2025, Kavaz 2023, Zhang 2022, Laouafi 2015, Yan 2013, Vallejo 2018, Tambing 2025):
  - They use measured plants abroad and often split data randomly or by ratio.
  - We test whole years in order and connect every forecast to a battery plan.
- **Philippine papers** (Luya 2016, Fronda 2017, Lin 2019, Garcia 2025, Fajardo 2020, Pao 2025, Salvador 2017):
  - They size systems in HOMER or genetic-algorithm tools, or simulate faults in Simulink.
  - None scores a day-ahead forecast.
- **Our honest gap:** our output is modeled, not metered. Deep networks and measured data are future work.

Full tables: `docs/RELATED_WORK.md` and the app's Methodology page.

## Deck corrections still needed (from the readiness review)

The Canva deck has to be edited by the team.

1. Remove the claim of an official NGCP demand dataset. Demand is a synthetic profile.
2. Replace the site-selection claims (the "ideal balanced maritime" Mactan benchmark and the Mindanao turbine cut-in claim). Say: three case coordinates, one per island group, chosen for comparison.
3. Check the solar AC equation slide against the paper's equation (2). The validation notes flag an extra sunlight multiplier.
4. Add these slides:
   - The fold grid (copy the Rolling test page).
   - The year-by-year MAE (Table IV in the paper).
   - The 2026 paired intervals (Table VII).
   - The grid-plan adjustment results (Table VIII).
   - The related-work comparison (Table I).
5. Keep the 2022 scenario outages separate from the forecast-evaluation replay.
6. Use the paper's title: *Day Ahead Forecasting of Modeled Solar and Wind Generation and Battery Planning in Three Philippine Locations*.

## Likely questions

- **Why only day-ahead?** Grid scheduling happens the day before. Beyond a few days, weather skill fades to "a typical month", which is what the Past-average baseline already is.
- **Do you click day by day?** No. The model forecasts every day automatically at midnight. The Rolling test calendar shows all of them at once.
- **Is this real plant data?** No. It is reference modeled output from NASA weather, so we compare methods fairly instead of claiming real-world accuracy.
- **Why not 2027?** A 2027 forecast would be a resource outlook from long-term averages, which is a separate task. Day-ahead skill does not validate a whole year.
- **How do we know 2026 was not used to train the 2026 model?** Open the 2026 forecast page.
  - The model saw 52,584 hours per site and source, from 2020 to 2025. Its last training hour is 31 Dec 2025 at 23:00.
  - The evaluation script has `assert refit.target_timestamp_pht.max() < test.target_timestamp_pht.min()`, so it cannot run with any overlap.
  - Each 2026 forecast is issued at 00:00 using only the previous day's output.
  - The computed 2026 output comes from 2026 NASA POWER weather. It is used once, to score.
  - The page recomputes the stored MAE (0.0953 MW at Laoag) from the hourly file. The 116 automated checks passed, including "test year only" and "issue midnight".
  - Paper: Fig. 6.
- **How do you prevent leakage?** Each forecast is issued at 00:00 using only the previous day. Settings are chosen on the year before the test, and test years never train or select anything.
- **Does it save money?** We don't claim savings. Lower grid-plan adjustment means less disagreement between the plan and what happened, which is the step before a cost study.
