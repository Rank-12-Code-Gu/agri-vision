"""Agri-Vision: Irrigation Decision Assistant (Streamlit).

Run from the project root:
    .venv/Scripts/python -m streamlit run app/app.py
Needs models/advisor.joblib (build with scripts/08_build_advisor.py).
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agrivision import economics as eco  # noqa: E402
from agrivision.heterogeneity import build_modifiers  # noqa: E402

FIG = ROOT / "outputs" / "figures"
HA_PER_ACRE = 1 / 2.471

st.set_page_config(page_title="Agri-Vision Irrigation Advisor", page_icon="🌾", layout="wide")


@st.cache_resource(show_spinner="Loading models...")
def load_bundle():
    return joblib.load(ROOT / "models" / "advisor.joblib")


B = load_bundle()
LV = B["levels"]
DIST = B["districts"].set_index("District")


def predict(profile: dict) -> dict:
    """Yield effect of the extra irrigation for one farm profile."""
    prof = pd.DataFrame([profile])
    X = build_modifiers(prof, LV).to_numpy()
    base = float(B["base_model"].predict(X)[0])
    out = {"baseline": base}
    for key, cf in B["forests"].items():
        e = float(cf.effect(X)[0])
        lo, hi = cf.effect_interval(X, alpha=0.10)
        out[key] = {"pct": 100 * np.expm1(e), "t_ha": base * np.expm1(e),
                    "lo_t_ha": base * np.expm1(float(lo[0])),
                    "hi_t_ha": base * np.expm1(float(hi[0]))}
    return out


# ------------------------------------------------------------------ header
st.title("🌾 Agri-Vision: Irrigation Decision Assistant")
st.caption("Should this wheat field get one extra irrigation at grain filling? "
           f"Evidence from {B['n_plots']:,} on-farm trial plots, 10 districts of Bihar and "
           f"eastern Uttar Pradesh, seasons {B['seasons'][0]} to {B['seasons'][-1]} "
           "(CIMMYT / CSISA open data).")

tab_adv, tab_map, tab_ev, tab_about = st.tabs(
    ["Advisor", "District view", "Evidence", "Method & limits"])

# ------------------------------------------------------------------ advisor
with tab_adv:
    left, right = st.columns([1, 1.6], gap="large")
    with left:
        st.subheader("Your field")
        district = st.selectbox("District", LV["District"],
                                index=LV["District"].index("Buxar"))
        lo_d, hi_d = B["sowing_day_range"]
        sow = st.date_input("Sowing date", value=dt.date(2025, 11, 15),
                            min_value=dt.date(2025, 10, 25), max_value=dt.date(2026, 1, 10),
                            help="Trial data cover sowing between "
                                 f"{(dt.date(2025, 1, 1) + dt.timedelta(lo_d - 1)):%d %b} and "
                                 f"{(dt.date(2025, 1, 1) + dt.timedelta(hi_d - 1)):%d %b}.")
        sow_day = sow.timetuple().tm_yday
        if sow.year > 2025:  # January sowing continues the day count
            sow_day += 365
        base_irr = st.select_slider("Irrigations already given (before this one)",
                                    options=[1, 2, 3, 4], value=3)
        tillage = st.radio("Sowing method", ["Zero tillage (ZT)", "Conventional (CT)"],
                           horizontal=True)
        c1, c2 = st.columns(2)
        soil = c1.selectbox("Soil type", LV["SoilType"],
                            index=LV["SoilType"].index(B["typical"]["SoilType"]))
        land = c2.selectbox("Land type", LV["LandType"],
                            index=LV["LandType"].index(B["typical"]["LandType"]))
        variety = st.selectbox("Variety", LV["VarietyGrp"],
                               index=LV["VarietyGrp"].index(B["typical"]["VarietyGrp"]))
        area = st.number_input("Field area (acres)", 0.1, 50.0, 1.0, 0.1)
        with st.expander("Prices and costs (edit for your situation)"):
            price = st.number_input("Wheat price (Rs/quintal)", 1000, 5000,
                                    eco.WHEAT_PRICE_RS_PER_QUINTAL, 25,
                                    help="Default = MSP assumption; verify current value.")
            cost_acre = st.number_input("Cost of one irrigation (Rs/acre)", 200, 5000,
                                        int(round(eco.IRRIGATION_COST_RS_PER_HA * HA_PER_ACRE, -1)),
                                        50, help="Diesel/electricity + pump + labour.")
    cost_ha = cost_acre / HA_PER_ACRE
    be = eco.break_even_gain_t_per_ha(price, cost_ha)

    profile = {"SowingDay": sow_day, "BaseIrrigations": base_irr,
               "ZeroTillage": 1 if tillage.startswith("Zero") else 0,
               "District": district, "SoilType": soil, "LandType": land,
               "VarietyGrp": variety}
    p = predict(profile)
    cons, corr, naive = p["conservative"], p["corrected"], p["naive"]

    MARGIN = 1.25  # cautious gain must beat break-even by 25% for a firm "yes"
    if cons["t_ha"] > MARGIN * be and corr["t_ha"] > be:
        verdict, colour, icon = "Give the extra irrigation", "#1b7f5a", "✅"
        why = "Even the most cautious estimate of the gain clearly pays for the irrigation."
    elif corr["t_ha"] > be:
        verdict, colour, icon = "Probably worth it", "#c98b2b", "🟡"
        why = ("The corrected estimate pays, but the most cautious one does not. "
               "Give it if water and money are available.")
    else:
        verdict, colour, icon = "Not worth it here", "#c0392b", "⛔"
        why = "The corrected gain does not cover the cost of the irrigation."

    ev = DIST.loc[district, "evidence"]
    with right:
        st.markdown(
            f"""<div style="border-left:8px solid {colour};padding:14px 18px;border-radius:8px;
            background:rgba(127,127,127,0.08)">
            <div style="font-size:1.6rem;font-weight:700">{icon} {verdict}</div>
            <div style="margin-top:4px">{why}</div>
            <div style="margin-top:6px;font-size:0.9rem;opacity:0.8">Evidence for {district}:
            <b>{ev}</b> ({int(DIST.loc[district, 'seasons_with_both_arms'])} seasons with both
            irrigated and control plots)</div></div>""", unsafe_allow_html=True)
        st.write("")

        lo_gain, hi_gain = cons["t_ha"], corr["t_ha"]
        q_lo, q_hi = lo_gain * 10 * area * HA_PER_ACRE, hi_gain * 10 * area * HA_PER_ACRE
        net_lo = eco.net_benefit_rs_per_ha(lo_gain, price, cost_ha) * area * HA_PER_ACRE
        net_hi = eco.net_benefit_rs_per_ha(hi_gain, price, cost_ha) * area * HA_PER_ACRE
        def rs(v):
            s = "-" if v < 0 else ""
            v = abs(v)
            return f"{s}₹{v / 1000:.1f}k" if v >= 1000 else f"{s}₹{v:.0f}"

        cards = [
            ("Extra grain (whole field)", f"{min(q_lo, q_hi):.1f}–{max(q_lo, q_hi):.1f} q"),
            ("Net profit (whole field)", f"{rs(min(net_lo, net_hi))} to {rs(max(net_lo, net_hi))}"),
            ("Yield without it", f"{p['baseline']:.2f} t/ha"),
        ]
        st.markdown(
            '<div style="display:flex;flex-wrap:wrap;gap:10px">' + "".join(
                f'<div style="flex:1 1 150px;padding:10px 14px;border-radius:8px;'
                f'background:rgba(127,127,127,0.10)"><div style="font-size:0.8rem;'
                f'opacity:0.75">{k}</div><div style="font-size:1.45rem;font-weight:700;'
                f'white-space:nowrap">{v}</div></div>' for k, v in cards) + "</div>",
            unsafe_allow_html=True)
        st.caption(f"Break-even gain at your price and cost: **{be:.2f} t/ha**. "
                   f"Cautious gain {cons['t_ha']:.2f}, corrected gain {corr['t_ha']:.2f} t/ha.")

        # gain chart
        bars = pd.DataFrame({
            "estimate": ["Cautious (ears & grain number removed)",
                         "Corrected (ear count removed)",
                         "Raw trial data (overstated)"],
            "gain": [cons["t_ha"], corr["t_ha"], naive["t_ha"]],
            "lo": [cons["lo_t_ha"], corr["lo_t_ha"], naive["lo_t_ha"]],
            "hi": [cons["hi_t_ha"], corr["hi_t_ha"], naive["hi_t_ha"]],
            "colour": ["#1b7f5a", "#2a6fb0", "#9e9e9e"]})
        fig = go.Figure()
        fig.add_bar(y=bars.estimate, x=bars.gain, orientation="h", marker_color=bars.colour,
                    error_x=dict(type="data", symmetric=False, array=bars.hi - bars.gain,
                                 arrayminus=bars.gain - bars.lo, color="#555"),
                    hovertemplate="%{x:.2f} t/ha<extra></extra>")
        bars["estimate"] = [f"{e}: <b>{g:.2f} t/ha</b>" for e, g in zip(bars.estimate, bars.gain)]
        fig.data[0].y = bars.estimate
        fig.add_vline(x=be, line_dash="dash", line_color="#c0392b",
                      annotation_text=f"break-even {be:.2f}", annotation_position="top")
        fig.update_layout(height=260, margin=dict(l=10, r=30, t=30, b=10),
                          xaxis_title="Yield gain from the extra irrigation (t/ha), 90% interval",
                          yaxis=dict(autorange="reversed"), showlegend=False)
        st.plotly_chart(fig, width="stretch")

        notes = []
        if not (lo_d <= sow_day <= hi_d):
            notes.append("Sowing date is outside the range seen in the trials, so the "
                         "estimate is an extrapolation.")
        if base_irr == 4:
            notes.append("Few trial farms had already given 4 irrigations (145 plots); the "
                         "gain is usually smaller for well-watered fields.")
        if soil == "Light":
            notes.append("Light soils are rare in the data (41 plots).")
        if ev == "Weak":
            notes.append(f"{district} has few seasons with comparable plots; treat the "
                         "district-specific part of this advice with caution.")
        notes.append("The raw trial gain (grey) is overstated: irrigated trial plots also had "
                     "13-15% more ears, which a late irrigation cannot cause. Advice uses the "
                     "corrected and cautious estimates.")
        with st.container(border=True):
            st.markdown("**Read before acting**")
            for n in notes:
                st.markdown(f"- {n}")

# ------------------------------------------------------------------ district view
with tab_map:
    st.subheader("Corrected gain by district")
    est_choice = st.radio("Estimate", ["Corrected", "Cautious", "Raw trial data"],
                          horizontal=True)
    col = {"Corrected": "corrected_t_ha", "Cautious": "conservative_t_ha",
           "Raw trial data": "naive_t_ha"}[est_choice]
    D = B["districts"].copy()
    D["gain"] = D[col].round(2)
    D["size"] = D.plots
    a, b = st.columns([1.4, 1], gap="large")
    with a:
        figm = px.scatter_map(D, lat="lat", lon="lon", color="gain", size="size",
                              hover_name="District",
                              hover_data={"gain": True, "evidence": True, "plots": True,
                                          "lat": False, "lon": False, "size": False},
                              color_continuous_scale="YlGn", range_color=(0, max(0.9, D.gain.max())),
                              zoom=6.1, center={"lat": 25.9, "lon": 85.2}, size_max=38,
                              map_style="carto-positron", height=470)
        figm.update_layout(margin=dict(l=0, r=0, t=0, b=0),
                           coloraxis_colorbar=dict(title="t/ha"))
        st.plotly_chart(figm, width="stretch")
    with b:
        tbl = D[["District", "gain", "evidence", "plots", "seasons_with_both_arms", "State"]]
        tbl = tbl.sort_values("gain", ascending=False).rename(columns={
            "gain": f"{est_choice} gain (t/ha)", "seasons_with_both_arms": "comparable seasons"})
        st.dataframe(tbl, hide_index=True, width="stretch")
        st.caption("Gains are averaged over each district's real trial farms. "
                   "Evidence: Strong = 5+ seasons with irrigated and control plots, "
                   "Moderate = 3-4, Weak = 2 or fewer.")

# ------------------------------------------------------------------ evidence
with tab_ev:
    st.subheader("How we got here: six steps of evidence")
    steps = [
        ("1. The trial data are uneven", "fig01_treatment_share_heatmap.png",
         "Some district-seasons irrigated every plot, others none: 14 of 56 cells have no "
         "comparison group. Treated and control plots differ on 24 of 44 farm variables."),
        ("2. Different methods give different answers", "fig08_baseline_forest.png",
         "Seven standard methods estimate between +0.71 and +1.12 t/ha from the same data."),
        ("3. A simulation shows which methods to trust", "fig10_sim_imbalance_dial.png",
         "With a known true effect, simple comparisons fail as imbalance grows; covariate-"
         "adjusting methods (Double ML family) stay accurate if all confounders are measured."),
        ("4. Who benefits? Validated heterogeneity", "fig13_gates_validation.png",
         "A causal forest's predicted winners really gain more on held-out farms (top fifth "
         "+1.26 vs bottom fifth +0.70 t/ha, raw scale)."),
        ("5. Heat does not explain it", "fig20_model_comparison.png",
         "NASA POWER grain-filling heat and rain do not change the benefit; district "
         "knowledge transfers to new seasons, weather does not."),
        ("6. Negative-control test reveals hidden confounding", "fig21_negative_control.png",
         "Irrigated plots had 13-15% more ears, impossible for an irrigation given ~108 days "
         "after sowing. Removing this channel gives a corrected gain of about 0.2-0.5 t/ha, "
         "still above break-even."),
    ]
    for title, img, text in steps:
        with st.container(border=True):
            c1, c2 = st.columns([1, 1.5], gap="large")
            c1.markdown(f"#### {title}")
            c1.write(text)
            if (FIG / img).exists():
                c2.image(str(FIG / img), width="stretch")

# ------------------------------------------------------------------ about
with tab_about:
    st.subheader("Method")
    st.markdown("""
- **Data:** Singh et al. (2023), *Large on-farm trial data to assess the effect of additional
  irrigation on yields of wheat ... in eastern India*, CIMMYT, hdl:11529/10548945.
- **Model:** causal forests (econml `CausalForestDML`), effect modifiers = district, sowing
  date, irrigations already given, tillage, soil, land type, variety; season, fertiliser,
  residue and location used as controls; cross-fitting grouped by block x season.
- **Correction for hidden confounding:** separate forests on yield per ear (corrected) and
  yield per grain (cautious), because irrigated plots had more ears than a late irrigation
  can cause.
- **Decision rule:** give the irrigation when the cautious gain beats break-even
  (cost / price); "probably" when only the corrected gain does.
""")
    st.subheader("Limits")
    st.markdown("""
- Trial plots were not randomised within fields; corrections assume the hidden difference
  acts through ear count and grain number. Effects remain approximate.
- Grain-filling heat did **not** explain differences in benefit, so advice is not adjusted
  for the weather forecast.
- Valid for Bihar / eastern UP wheat with 1-4 prior irrigations and sowing 1 Nov - 27 Dec.
- Prices and costs are user inputs; defaults are assumptions.
""")
    st.caption(f"Models built {B['built']}. Code: scripts/01-08, src/agrivision.")
