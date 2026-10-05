# Related work comparison

Summarised from the IEEE papers the team collected (`~/Downloads/IEEE`). The same tables appear on the app's Methodology page (`solwind/literature.py`). Paper references [11] and [16]–[27] cover these studies.

## Forecasting studies

| Study | Venue | Where | Data | Task | Method | Test split | Planning link |
|---|---|---|---|---|---|---|---|
| Hu et al. | EEICE 2025 | Province in China | Measured farm output, 2020, 15 min | Ultra-short-term power | CNN-BiLSTM-Attention | 7:3 split | No |
| Kavaz & Karazor | ICPSE 2023 | Denmark, one co-located plant | Measured, 15 months | 24 h ahead from previous 24 h | RF, boosting incl. XGBoost, LSTM, CNN-LSTM-Attention | 70 / 20 / 10 | No |
| Zhang, Han et al. | CIEEC 2022 | Southern China, 8 wind and 6 PV stations | NWP + measured, 1 year, 15 min | Short-term, regional joint | Attention neural network | Held-out 54 days | No |
| Zhang, Zheng et al. | TELEPE 2025 | Hubei, China | Measured generation and load | Joint generation + load | GRU-CNN with attention | Not chronological by year | Scheduling motivation |
| Yan et al. | SOLI 2013 | Zhangjiakou demo, China | Turbine-level NWP + monitoring | Next day and next 4 h | NWP + statistical ensemble | Monthly accuracy | Grid requirement |
| Laouafi et al. | IREC 2015 | Mainland France | RTE 15 min, 2013–2014 | 1 h ahead load, wind, solar | Feed-forward neural network | Hold-out period | No |
| Vallejo et al. | EPIM 2018 | Uruguay | Met-service forecasts + farm output | Medium-term, 168 h | GA-trained neural network | Chronological 70/30 | Market operator use |
| Tambing et al. | ICISS 2025 | Jakarta, Indonesia | Daily weather, 2024 | Irradiance → panel sizing | LSTM | 85:15 split | PV + battery sizing |
| This work | CSS142 2026 | Laoag, Mactan, General Santos | NASA POWER hourly 2020–Jun 2026, modeled output | Day-ahead, 24 h issued 00:00 | XGBoost vs previous day and climatology | Rolling years: 2024, 2025, Jan–Jun 2026 | Battery grid-plan replay |

## Philippine planning and simulation studies

| Study | Venue | Focus | Tool | Relation to this work |
|---|---|---|---|---|
| Salvador & Manalo | ICSEng 2017 | Wind-solar farm for a combined-cycle plant outage | MATLAB Simscape | Outage scenario; motivates our outage tests |
| Luya, Gan & Pedrasa | ISGT-Asia 2016 | 8,760-hour microgrid simulator: interruptions, energy not supplied | Custom tool | Same hourly energy-balance idea, no forecasting |
| Fronda, Rosendo & Pedrasa | ISGT-Asia 2017 | Isolated microgrid sizing under cost or reliability targets | Genetic algorithm | Sizing, not forecast evaluation |
| Lin, Phan & Lai | SoutheastCon 2019 | Basco island PV-wind-diesel-battery design | HOMER | Economic sizing from monthly resource |
| Garcia & Gacu | CICN 2025 | Sibuyan Island hybrid options, 9,000+ simulations | HOMER Pro | Economic sizing, no hourly forecast |
| Fajardo et al. | HNICEM 2020 | PV + wind + BESS microgrid under faults | MATLAB Simulink, t-test | Electrical stability, outside our energy scope |
| Pao et al. | HNICEM 2025 | PV output across Philippine climates | Simulink, exergy analysis | Cooler sites favour PV; we hold equipment fixed |
| Acuzar et al. | IEEE 2017 | Weather and climate effects on Visayas generation | HOMER | Annual resource, not day-ahead |

## What this means for the defense

- Most forecasting papers use a ratio split or one hold-out period. This work tests whole years in order, so the model never sees the future.
- They use measured output from one plant or one region abroad. This work compares three Philippine island groups with identical equipment, but the output is modeled.
- Philippine studies mostly size systems in HOMER or simulate electrical faults. None evaluates a day-ahead forecast against a battery plan.
- Deep networks (CNN-BiLSTM, attention) report gains on measured data. This work uses gradient boosting with two simple baselines, and adding deep models is listed as future work.

## Collected but not cited

These were in the folder but fall outside the paper's scope:

- Lasay & Ang, PSGEC 2025: fuzzy control of a multi-input LLC converter (power electronics).
- Salvador et al., ICSEng 2017: small Savonius turbine for sensor nodes (device scale).
- Abutin et al., TENSYMP 2021: genetic-algorithm DG placement on the IEEE 33-bus system (power flow).
- Abanes et al., ICCAD 2025: energy-harvesting circuit simulation in Multisim.
- Zia et al., NAPS 2023: irradiance beneath panels for agrivoltaics.
- Platonova et al., UralCon 2019: solar energy input to tilted panels (supports the plane-of-array step, but the paper already cites NOAA and pvlib).
- Hamid et al., 2009: Hurst exponents of the geomagnetic field. This paper is unrelated to solar or wind generation.
- Acuzar et al., 2017 (Visayas, HOMER): relevant, but its venue could not be verified from the PDF, so it is shown in the app only and not cited in the paper.
