"""Does grain-filling heat (or rain) explain who benefits from the extra irrigation?

Run from the project root:
    .venv/Scripts/python scripts/06_weather_test.py
Needs internet the first time (NASA POWER); afterwards uses data/external cache.
Writes figures 18-20, tables, outputs/weather_test_summary.md.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agrivision import estimators as est  # noqa: E402
from agrivision import heterogeneity as het  # noqa: E402
from agrivision import weather as wxm  # noqa: E402
from agrivision.data import design_matrix, load_clean  # noqa: E402

FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"
plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 10})
GREEN, RED, GREY = "#1b7f5a", "#c0392b", "#8c8c8c"
Z = 1.959963984540054
t0 = time.time()

df = load_clean()
wx = wxm.fetch_all(df)
df = df.join(wxm.plot_exposure(df, wx))
WEATHER = ["GF_TmaxMean", "GF_HeatDays", "GF_RainMM", "GF_TminMean"]

nu = est.cross_fit_nuisance(df, design_matrix(df), seed=0)
df["psi"] = het.dr_scores(df, nu)
CL = "DistrictYear"  # weather varies at this level -> cluster here (conservative)

# ------------------------------------------------------------------ 1. descriptive
wx_tab = df.groupby(["District", "Year"])[["GF_TmaxMean", "GF_HeatDays", "GF_RainMM"]].mean()
wx_tab.round(2).to_csv(TAB / "weather_by_district_season.csv")
var_share = {}
for v in ["GF_HeatDays", "GF_RainMM", "GF_TmaxMean"]:
    tot = df[v].var()
    var_share[v] = {
        "share_explained_by_season": smf.ols(f"{v} ~ C(Year)", df).fit().rsquared,
        "share_explained_by_district": smf.ols(f"{v} ~ C(District)", df).fit().rsquared,
    }
var_share = pd.DataFrame(var_share).T

# ------------------------------------------------------------------ 2. effect-modification regressions
d = df.copy()
for v in WEATHER:
    d[v + "_z"] = (d[v] - d[v].mean()) / d[v].std()
fit = lambda f: smf.ols(f, d).fit(cov_type="cluster",  # noqa: E731
                                  cov_kwds={"groups": pd.factorize(d[CL])[0]})
m_heat = fit("psi ~ GF_HeatDays_z")
m_hr = fit("psi ~ GF_HeatDays_z + GF_RainMM_z")
m_tmax = fit("psi ~ GF_TmaxMean_z + GF_RainMM_z")
m_dist = fit("psi ~ C(District)")
m_dw = fit("psi ~ C(District) + GF_HeatDays_z + GF_RainMM_z")
m_season = fit("psi ~ C(Year)")

dist_terms = [p for p in m_dw.params.index if p.startswith("C(District)")]
wald_dist = m_dw.wald_test(" , ".join(f"{p} = 0" for p in dist_terms), scalar=True)
wald_wx = m_dw.wald_test("GF_HeatDays_z = 0, GF_RainMM_z = 0", scalar=True)
spread_before = float(np.std(m_dist.params[dist_terms]))
spread_after = float(np.std(m_dw.params[dist_terms]))


def coef_row(m, name, label):
    return {"model": label, "term": name, "coef_t_per_ha_per_SD": m.params[name],
            "ci_low": m.conf_int().loc[name, 0], "ci_high": m.conf_int().loc[name, 1],
            "p": m.pvalues[name]}


reg = pd.DataFrame([
    coef_row(m_heat, "GF_HeatDays_z", "heat days only"),
    coef_row(m_hr, "GF_HeatDays_z", "heat days + rain"),
    coef_row(m_hr, "GF_RainMM_z", "heat days + rain"),
    coef_row(m_tmax, "GF_TmaxMean_z", "mean Tmax + rain"),
    coef_row(m_tmax, "GF_RainMM_z", "mean Tmax + rain"),
    coef_row(m_dw, "GF_HeatDays_z", "district FE + heat + rain (within district)"),
    coef_row(m_dw, "GF_RainMM_z", "district FE + heat + rain (within district)"),
])
reg.to_csv(TAB / "weather_effect_modification.csv", index=False)

# ------------------------------------------------------------------ 3. window / threshold sensitivity
sens = []
for (a, b) in [(85, 115), (95, 125), (105, 135)]:
    for thr in [32.0, 34.0, 36.0]:
        ex = wxm.plot_exposure(df, wx, a, b, thr)
        s = d[["psi", CL]].copy()
        s["heat_z"] = (ex.GF_HeatDays - ex.GF_HeatDays.mean()) / ex.GF_HeatDays.std()
        s["rain_z"] = (ex.GF_RainMM - ex.GF_RainMM.mean()) / ex.GF_RainMM.std()
        m = smf.ols("psi ~ heat_z + rain_z", s).fit(
            cov_type="cluster", cov_kwds={"groups": pd.factorize(s[CL])[0]})
        sens.append({"window_DAS": f"{a}-{b}", "threshold_C": thr,
                     "heat_coef": m.params["heat_z"], "heat_p": m.pvalues["heat_z"],
                     "rain_coef": m.params["rain_z"], "rain_p": m.pvalues["rain_z"]})
sens = pd.DataFrame(sens)
sens.to_csv(TAB / "weather_window_sensitivity.csv", index=False)
print(f"regressions done ({time.time() - t0:.0f}s)")

# ------------------------------------------------------------------ 3b. district cross-check
# Simple, stable estimator per district: compare plots within the same season of that
# district, adjusting for practice. Guards against unstable doubly robust scores.
Xall = design_matrix(df)
keep_cols = [c for c in Xall.columns if not c.startswith(("Year_", "District_"))]
dist_check = []
for dname, g in df.groupby("District"):
    g = g[g.groupby("Year").Treated.transform(lambda v: 0 < v.mean() < 1)]
    if g.Treated.nunique() < 2:
        continue
    Xg = Xall.loc[g.index, keep_cols]
    Xg = Xg.loc[:, Xg.std() > 0]
    fe = pd.get_dummies(g.Year, drop_first=True, dtype=float, prefix="Y")
    Xd = pd.concat([g[["Treated"]].astype(float), Xg, fe], axis=1)
    import statsmodels.api as sm
    r = sm.OLS(g.GrainYield, sm.add_constant(Xd)).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(g.ClusterBlockYear)[0]})
    dist_check.append({"District": dname, "n": len(g), "seasons": g.Year.nunique(),
                       "within_season_effect": r.params["Treated"],
                       "ci_low": r.conf_int().loc["Treated", 0],
                       "ci_high": r.conf_int().loc["Treated", 1],
                       "dr_score_mean": df.loc[df.District == dname, "psi"].mean()})
dist_check = pd.DataFrame(dist_check).sort_values("within_season_effect")
dist_check.to_csv(TAB / "district_effects_crosscheck.csv", index=False)

# ------------------------------------------------------------------ 4. forest comparison
practice_num = het.MODIFIER_NUMERIC
practice_cat = ["SoilType", "LandType", "VarietyGrp"]
specs = {
    "Practice only": (practice_num, practice_cat),
    "District + practice": (practice_num, practice_cat + ["District"]),
    "Weather + practice": (practice_num + WEATHER, practice_cat),
    "District + weather + practice": (practice_num + WEATHER, practice_cat + ["District"]),
}
W = het.build_controls(df)


def evaluate(oof):
    s = pd.DataFrame({"psi": df.psi, "c": oof - oof.mean(), "g": df[CL]})
    m = smf.ols("psi ~ c", s).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(s.g)[0]})
    q = pd.qcut(oof, 5, labels=False, duplicates="drop")
    gap = df.psi[q == q.max()].mean() - df.psi[q == 0].mean()
    return m.params["c"], m.bse["c"], m.pvalues["c"], gap


comp = []
for name, (num, cat) in specs.items():
    levels = het.modifier_levels(df, cat)
    Xm = het.build_modifiers(df, levels, numeric=num)
    for scheme, split_by, k in [("new locality", "ClusterBlockYear", 5),
                                ("new season", "Year", 6)]:
        oof = het.out_of_fold_cate(df, Xm, W, n_splits=k, seed=0, split_by=split_by)
        slope, se, p, gap = evaluate(oof)
        comp.append({"model": name, "validation": scheme, "calibration_slope": slope,
                     "slope_se": se, "slope_p": p, "top_minus_bottom_quintile": gap})
        print(f"  {name:32s} {scheme:13s} slope {slope:.2f} p {p:.3f} ({time.time() - t0:.0f}s)")
comp = pd.DataFrame(comp)
comp.to_csv(TAB / "forest_model_comparison.csv", index=False)

# ------------------------------------------------------------------ figures
cells = (df.groupby(["District", "Year"])
         .agg(n=("psi", "size"), share=("Treated", "mean"), effect=("psi", "mean"),
              heat=("GF_HeatDays", "mean"), rain=("GF_RainMM", "mean")).reset_index())
cells = cells[(cells.share > 0) & (cells.share < 1)]
cells.to_csv(TAB / "district_season_effects.csv", index=False)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.3), sharey=True)
cmap = plt.get_cmap("tab10")
dists = sorted(cells.District.unique())
for ax, var, lab in [(axes[0], "heat", "Heat days (Tmax > 34 C) in grain filling"),
                     (axes[1], "rain", "Rain during grain filling (mm)")]:
    for i, dd in enumerate(dists):
        c = cells[cells.District == dd]
        ax.scatter(c[var], c.effect, s=c.n * 1.5, color=cmap(i % 10), alpha=0.75,
                   label=dd if var == "heat" else None, edgecolor="white")
    w = np.polyfit(cells[var], cells.effect, 1, w=np.sqrt(cells.n))
    xs = np.linspace(cells[var].min(), cells[var].max(), 50)
    ax.plot(xs, np.polyval(w, xs), color="#333", lw=1.2, ls="--")
    ax.axhline(0, color=GREY, lw=0.6)
    ax.set_xlabel(lab)
axes[0].set_ylabel("Measured gain in that district-season (t/ha)")
axes[0].legend(fontsize=7, frameon=False, ncol=2, loc="upper left")
fig.suptitle("Does weather explain where the extra irrigation helps most?\n"
             "(each bubble = one district-season with both arms; size = plots)")
fig.tight_layout()
fig.savefig(FIG / "fig18_effect_vs_weather.png")
plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 3.6))
yrs = df.groupby("Year")[["GF_HeatDays", "GF_RainMM"]].mean()
ax.bar(yrs.index, yrs.GF_HeatDays, color=RED, alpha=0.8, label="Heat days > 34 C")
ax2 = ax.twinx()
ax2.plot(yrs.index, yrs.GF_RainMM, "o-", color="#2a6fb0", label="Rain (mm)")
ax.set_ylabel("Heat days in grain filling")
ax2.set_ylabel("Rain in grain filling (mm)")
ax.set_title("Grain-filling weather by season (NASA POWER)")
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, frameon=False, loc="upper right")
fig.tight_layout()
fig.savefig(FIG / "fig19_weather_by_season.png")
plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
for ax, scheme in zip(axes, ["new locality", "new season"]):
    c = comp[comp.validation == scheme]
    y = np.arange(len(c))[::-1]
    ax.errorbar(c.calibration_slope, y, xerr=Z * c.slope_se, fmt="o", color=GREEN,
                ecolor="#555", capsize=3)
    ax.axvline(0, color=GREY, lw=0.8); ax.axvline(1, color=RED, lw=0.8, ls="--")
    ax.set_yticks(y, c.model)
    ax.set_xlabel("Calibration slope (1 = perfect, 0 = no skill)")
    ax.set_title(f"Predicting a {scheme}")
fig.suptitle("Which information predicts who benefits? (out-of-fold, 95% CI)")
fig.tight_layout()
fig.savefig(FIG / "fig20_model_comparison.png")
plt.close(fig)

# ------------------------------------------------------------------ summary
L = ["# Agri-Vision - Weather Test: does grain-filling heat explain who benefits?", "",
     f"Weather: NASA POWER daily (MERRA-2), 25 grid cells. Grain-filling window = "
     f"{wxm.GF_START_DAS}-{wxm.GF_END_DAS} days after each plot's sowing date; heat day = "
     f"Tmax > {wxm.HEAT_THRESHOLD_C:.0f} C. Effect measured with doubly robust scores; "
     "SEs clustered by district x season (the level at which weather varies).", "",
     "## 1. Where does weather vary?", "", var_share.round(3).to_markdown(), "",
     "Season-by-season means:", "",
     df.groupby("Year")[["GF_TmaxMean", "GF_HeatDays", "GF_RainMM"]].mean().round(2).to_markdown(),
     "", "## 2. Does weather change the effect? (per 1 SD of the weather variable)", "",
     reg.round(3).to_markdown(index=False), "",
     f"- 1 SD = {df.GF_HeatDays.std():.1f} heat days; {df.GF_RainMM.std():.1f} mm rain.",
     "", "## 3. Do weather differences explain the district differences?", "",
     f"- Spread (SD) of district effects: {spread_before:.3f} t/ha without weather -> "
     f"{spread_after:.3f} with heat + rain.",
     f"- District effects still jointly significant after adding weather: "
     f"p = {float(wald_dist.pvalue):.3g}.",
     f"- Weather jointly significant after district: p = {float(wald_wx.pvalue):.3g}.",
     f"- R2 of effect scores: district {m_dist.rsquared:.3f}, season {m_season.rsquared:.3f}, "
     f"heat+rain {m_hr.rsquared:.3f}, district+heat+rain {m_dw.rsquared:.3f}.", "",
     "### District cross-check (within-season regression per district, practice-adjusted)", "",
     dist_check.round(3).to_markdown(index=False), "",
     "## 4. Robustness to window and threshold", "",
     sens.round(3).to_markdown(index=False), "",
     "## 5. Causal-forest comparison (out-of-fold calibration)", "",
     comp.round(3).to_markdown(index=False), "",
     "## District-season cells used in Figure 18", "",
     cells.round(2).to_markdown(index=False), ""]
(ROOT / "outputs" / "weather_test_summary.md").write_text("\n".join(L), encoding="utf-8")
print("\n".join(L))
print(f"total {time.time() - t0:.0f}s")
