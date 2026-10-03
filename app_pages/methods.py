import pandas as pd
import streamlit as st

from habagat import dispatch, theme
from habagat.physics import ASSUMPTIONS

theme.header(
    "Methods",
    "The equations <em>behind every pixel</em>",
    "Habagat runs the same code as the research paper. The test suite checks that the five-year energy totals and battery "
    "coverage match the published tables exactly.",
)

solar, wind, storage, forecast = st.tabs(["Solar PV", "Wind turbine", "Battery", "Forecasting"])
with solar:
    st.markdown("**Sun position** · NOAA fractional-year method at each hour’s midpoint")
    st.latex(r"\gamma = \tfrac{2\pi}{N}\left(d - 1 + \tfrac{h_{mid}-12}{24}\right),\qquad "
             r"\cos\theta_z = \sin\phi\sin\delta + \cos\phi\cos\delta\cos\omega")
    st.markdown("**Plane-of-array irradiance** · fixed 10° tilt, facing south, isotropic sky")
    st.latex(r"\cos\theta_i = \sin\delta\sin(\phi-\beta) + \cos\delta\cos(\phi-\beta)\cos\omega")
    st.latex(r"E_{poa} = DNI\,\max(\cos\theta_i,0) + DHI\,\tfrac{1+\cos\beta}{2} + GHI\,\rho_g\,\tfrac{1-\cos\beta}{2}")
    st.markdown("**Cell temperature** (Faiman) and **power**")
    st.latex(r"T_{cell} = T_{air} + \frac{E_{poa}}{U_0 + U_1\,v_{2m}},\qquad v_{2m} = v_{10}\left(\tfrac{2}{10}\right)^{\alpha}")
    st.latex(r"P_{dc} = P_{rated}\,\frac{E_{poa}}{1000}\,\big[1 + \gamma_p (T_{cell}-25)\big],\qquad "
             r"P_{ac} = \min\!\big(P_{dc}(1-L)\,\eta_{inv},\; P_{ac,max}\big)")
with wind:
    st.markdown("**Hub-height wind** from the 50 m reanalysis wind (power-law shear)")
    st.latex(r"v_{hub} = v_{50}\left(\tfrac{69}{50}\right)^{\alpha}")
    st.markdown("**Air-density correction** (ideal gas, site-corrected pressure)")
    st.latex(r"\rho = \frac{p}{R_d\,T},\qquad v_{adj} = v_{hub}\left(\frac{\rho}{1.225}\right)^{1/3}")
    st.markdown("**Turbine output** · EWT DW61 1 MW theoretical curve (NLR turbine-models), with a net-output factor")
    st.latex(r"P_{wind} = f_{net}\cdot \mathrm{PowerCurve}(v_{adj}),\qquad P_{wind}=0 \text{ above cut-out}")
with storage:
    st.markdown(
        f"One-hour steps. {dispatch.BATTERY_POWER_MW:g} MW power limit, "
        f"{dispatch.CHARGE_EFFICIENCY:.0%} charge / {dispatch.DISCHARGE_EFFICIENCY:.0%} discharge efficiency, "
        f"state of charge kept between {dispatch.MIN_SOC_FRACTION:.0%} and {dispatch.MAX_SOC_FRACTION:.0%}."
    )
    st.latex(r"c_t = \min\!\left(S_t,\; P_b,\; \tfrac{SOC_{max}-SOC_t}{\eta_c}\right),\qquad "
             r"d_t = \min\!\big(D_t,\; P_b,\; (SOC_t - SOC_{min})\,\eta_d\big)")
    st.latex(r"SOC_{t+1} = SOC_t + \eta_c c_t - \tfrac{d_t}{\eta_d},\qquad g_t = D_t - d_t")
    st.markdown("$S_t$ is surplus and $D_t$ is deficit versus demand. $g_t$ is grid energy, "
                "or unmet demand during an outage drill.")
    hours = pd.Series(range(24))
    st.bar_chart(pd.DataFrame({"hour": hours, "demand MW": dispatch.synthetic_load_mw(hours)}).set_index("hour"),
                 color=theme.INK, height=200)
    st.caption("The standardized demand scenario used at every site (×1.0).")
with forecast:
    st.markdown(
        "- **Issue time** 00:00 Philippine time, **horizon** 24 hours, **inputs** the previous 24 hours plus calendar features.\n"
        "- **Split** train 2020–2023 · validate 2024 · test 2025 (scored once).\n"
        "- **Methods** XGBoost (one model per site and source, seed 142) · previous-day persistence · "
        "training-period hourly-monthly climatology."
    )
    st.latex(r"\mathrm{MAE} = \frac{1}{n}\sum_t |\hat y_t - y_t|,\qquad \mathrm{RMSE} = \sqrt{\frac{1}{n}\sum_t (\hat y_t - y_t)^2}")
    st.markdown("**Grid-plan adjustment** for each hour: extra grid energy needed beyond the plan, plus planned energy that "
                "was not needed. Summed over 8,760 hours.")

theme.header("Assumptions", "Fixed parameters")
st.dataframe(
    pd.DataFrame({"Parameter": list(ASSUMPTIONS), "Value": [str(v) for v in ASSUMPTIONS.values()]}),
    hide_index=True, width="stretch", height=320,
)

theme.header("Sources", "Data and references")
st.markdown(
    """
- NASA POWER hourly API, v2.10 — [power.larc.nasa.gov](https://power.larc.nasa.gov/docs/services/api/temporal/hourly/)
- NOAA solar position equations — [gml.noaa.gov](https://gml.noaa.gov/grad/solcalc/solareqns.PDF)
- PVWatts v5 technical reference — [pvwatts.nrel.gov](https://pvwatts.nrel.gov/downloads/pvwattsv5.pdf)
- pvlib isotropic POA and Faiman temperature models — [pvlib-python.readthedocs.io](https://pvlib-python.readthedocs.io/)
- EWT DW61 datasheet — [ewtdirectwind.com](https://ewtdirectwind.com/wp-content/uploads/2023/11/EWT_DW61.pdf)
- EWT DW61 1 MW power curve, NLR turbine-models (BSD-3; licence in `data/`) — [github.com/NatLabRockies/turbine-models](https://github.com/NatLabRockies/turbine-models)
"""
)

theme.header("Limits", "Read the results with these in mind")
theme.html(
    """<div class="hb-two">
<div class="hb-card"><h5>Data</h5><ul>
<li>NASA POWER is gridded reanalysis, not on-site measurement.</li>
<li>Generation is <i>reference modeled</i> output, not metered plant data.</li>
<li>Demand is one standardized scenario at all sites, not measured NGCP or city load.</li></ul></div>
<div class="hb-card"><h5>Scope</h5><ul>
<li>Hourly energy balance only: no voltage, frequency, ramping limits or protection.</li>
<li>No equipment failures, degradation, typhoon damage or repair times.</li>
<li>Planning replay assumes the grid can always adjust in real time. It does not imply lower real-world cost.</li></ul></div>
</div>"""
)
