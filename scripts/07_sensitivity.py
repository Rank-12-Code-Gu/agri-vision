"""How sure are we? Hidden-confounding checks for the extra-irrigation effect.

Part A - Negative-control outcomes (design-based, uses agronomy):
  The extra irrigation was applied at a median ~108 days after sowing (dough stage),
  after the number of ears (effective tillers) was fixed. It cannot create ears.
  So any adjusted "effect" on tiller count reveals hidden differences between plots.
  Grain yield = ears x grains/ear x grain weight, so effects on log(yield per ear)
  remove the ear-count channel.

Part B - Formal sensitivity bounds (Cinelli & Hazlett 2020, PySensemakr):
  How strong would an unmeasured confounder have to be, compared with measured ones,
  to explain away the effect?

Part C - The same checks for the district differences.

Run from the project root:
    .venv/Scripts/python scripts/07_sensitivity.py
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
import sensemakr as smk
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agrivision import estimators as est  # noqa: E402
from agrivision.data import IRRIGATION_DAY_COLS, design_matrix, load_clean  # noqa: E402

FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"
plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 10})
GREEN, RED, GREY, BLUE = "#1b7f5a", "#c0392b", "#8c8c8c", "#2a6fb0"
Z = 1.959963984540054
t0 = time.time()

df = load_clean()
sow = pd.to_datetime(df.SowingDate.astype(str), format="%Y.%m.%d")
df["ExtraIrrigationDAS"] = np.where(df.Treated == 1, df[IRRIGATION_DAY_COLS].max(axis=1), np.nan)
df["logYield"] = np.log(df.GrainYield)
df["logEars"] = np.log(df.TillersCount)
df["logGrainsPerEar"] = np.log(df.GrainsCount)
df["logGrainWeight"] = np.log(df.TestWeight)
df["logBiomass"] = np.log(df.BiomassYield)
df["logYieldPerEar"] = df.logYield - df.logEars
df["logYieldPerGrain"] = df.logYield - df.logEars - df.logGrainsPerEar

OUTCOMES = [
    ("logYield", "Grain yield", "target"),
    ("logEars", "Ears (effective tillers) per m - CANNOT be caused", "negative control"),
    ("logGrainsPerEar", "Grains per ear - mostly fixed before irrigation", "near-negative control"),
    ("logGrainWeight", "1000-grain weight - grain-filling channel", "plausible channel"),
    ("logBiomass", "Total biomass", "mixed"),
    ("logYieldPerEar", "Yield per ear (ear-count channel removed)", "calibrated target"),
    ("logYieldPerGrain", "Yield per grain (ears and grains removed)", "calibrated target"),
]


def pct(b):
    return 100 * (np.exp(b) - 1)


# ------------------------------------------------------------------ A. negative controls
def effects_for(data, label):
    X = design_matrix(data)
    rows = []
    for col, name, role in OUTCOMES:
        d = data.copy()
        d["GrainYield"] = d[col]  # estimators read GrainYield
        r_fe = est.ols_district_year_fe(d, X)
        nu = est.cross_fit_nuisance(d, X, seed=0)
        r_dml = est.dml_plr(d, nu)
        for r, m in [(r_fe, "District x season FE regression"), (r_dml, "Double ML")]:
            rows.append({"sample": label, "outcome": name, "role": role, "method": m,
                         "pct_effect": pct(r["estimate"]), "ci_low": pct(r["ci_low"]),
                         "ci_high": pct(r["ci_high"]), "n": r["n"]})
    return rows


neg = effects_for(df, "all plots")
late = df[(df.Treated == 0) | (df.ExtraIrrigationDAS >= 100)].reset_index(drop=True)
neg += effects_for(late, "extra irrigation >= 100 DAS only")
neg = pd.DataFrame(neg)
neg.to_csv(TAB / "negative_control_outcomes.csv", index=False)
print(f"negative controls done ({time.time() - t0:.0f}s)")

# yield-level translation of the calibrated estimate (FE regression, all plots)
ctrl_mean = df.loc[df.Treated == 0, "GrainYield"].mean()


def get(outcome_prefix, method="District x season FE regression", sample="all plots"):
    r = neg[(neg.outcome.str.startswith(outcome_prefix)) & (neg.method == method)
            & (neg["sample"] == sample)].iloc[0]
    return r


cal_rows = []
for prefix, label in [("Grain yield", "Uncorrected"),
                      ("Yield per ear", "Ear-count channel removed"),
                      ("Yield per grain", "Ear + grain-number channels removed")]:
    for method in ["District x season FE regression", "Double ML"]:
        r = get(prefix, method)
        cal_rows.append({"estimate": label, "method": method, "pct": r.pct_effect,
                         "t_per_ha_at_control_mean": ctrl_mean * r.pct_effect / 100,
                         "ci_low_t": ctrl_mean * r.ci_low / 100,
                         "ci_high_t": ctrl_mean * r.ci_high / 100})
cal = pd.DataFrame(cal_rows)
cal.to_csv(TAB / "calibrated_effect.csv", index=False)

# ------------------------------------------------------------------ B. sensemakr
X = design_matrix(df)
dy = pd.get_dummies(df.DistrictYear, drop_first=True, dtype=float, prefix="DY")
Xb = X.drop(columns=[c for c in X.columns if c.startswith(("Year_", "District_"))])
Xfull = sm.add_constant(pd.concat([df[["Treated"]].astype(float), Xb, dy], axis=1))
ols_y = sm.OLS(df.GrainYield, Xfull).fit()
ols_d = sm.OLS(df.Treated.astype(float), Xfull.drop(columns="Treated")).fit()

b_hat, se_hat, dof = float(ols_y.params["Treated"]), float(ols_y.bse["Treated"]), int(ols_y.df_resid)
r2yd = smk.partial_r2(t_statistic=np.array([ols_y.tvalues["Treated"]]), dof=dof)
rv = smk.robustness_value(t_statistic=np.array([ols_y.tvalues["Treated"]]), dof=dof, q=1)
rv_a = smk.robustness_value(t_statistic=np.array([ols_y.tvalues["Treated"]]), dof=dof, q=1, alpha=0.05)
# how much of the effect must be explained to fall to the ear-calibrated value?
q_cal = 1 - (ctrl_mean * get("Yield per ear").pct_effect / 100) / b_hat
rv_cal = smk.robustness_value(t_statistic=np.array([ols_y.tvalues["Treated"]]), dof=dof, q=float(q_cal))

groups = {
    "Irrigations already given": ["BaseIrrigations"],
    "Sowing day": ["SowingDay"],
    "Fertiliser practice (8 vars)": ["BasalDAP_f", "BasalMOP", "Split1Urea", "Split2Urea",
                                     "Split3Urea_f", "UsedDAP", "UsedNPK", "UsedZn"],
    "District x season (56 cells)": list(dy.columns),
}
def benchmark_bound(r2dxj, r2yxj, kd, ky):
    """Cinelli & Hazlett (2020) benchmark bound - same formula as PySensemakr's
    ovb_partial_r2_bound, re-implemented because that function crashes on scalars
    when the implied bound exceeds 1. Returns (r2dz_x, r2yz_dx) or None if impossible."""
    r2dz = kd * r2dxj / (1 - r2dxj)
    if r2dz >= 1:
        return None
    r2zxj = kd * r2dxj ** 2 / ((1 - kd * r2dxj) * (1 - r2dxj))
    if r2zxj >= 1:
        return None
    r2yz = ((np.sqrt(ky) + np.sqrt(r2zxj)) / np.sqrt(1 - r2zxj)) ** 2 * (r2yxj / (1 - r2yxj))
    return float(r2dz), float(min(r2yz, 1.0))


bench = []
for gname, cols in groups.items():
    if len(cols) == 1:
        r2dxj = smk.partial_r2(t_statistic=np.array([ols_d.tvalues[cols[0]]]), dof=int(ols_d.df_resid))
        r2yxj = smk.partial_r2(t_statistic=np.array([ols_y.tvalues[cols[0]]]), dof=dof)
    else:
        def grp(m, cs):
            ft = m.f_test(" , ".join(f"{c} = 0" for c in cs))
            return smk.group_partial_r2(f_statistic=float(ft.fvalue), p=len(cs),
                                        dof=int(m.df_resid))
        r2dxj, r2yxj = grp(ols_d, cols), grp(ols_y, cols)
    for k in (1, 2, 3):
        r2dxj_f, r2yxj_f = float(np.ravel(r2dxj)[0]), float(np.ravel(r2yxj)[0])
        bnd = benchmark_bound(r2dxj_f, r2yxj_f, k, k)
        if bnd is None:
            bench.append({"benchmark": gname, "k_times_as_strong": k,
                          "r2_with_treatment": np.nan, "r2_with_yield": np.nan,
                          "adjusted_effect_t_ha": np.nan, "adj_ci_low": np.nan,
                          "adj_ci_high": np.nan})
            continue
        r2dz, r2yz = bnd
        adj = float(np.ravel(smk.adjusted_estimate(r2dz, r2yz, estimate=b_hat, se=se_hat,
                                                   dof=dof))[0])
        adj_se = float(np.ravel(smk.adjusted_se(r2dz, r2yz, se=se_hat, dof=dof))[0])
        bench.append({"benchmark": gname, "k_times_as_strong": k,
                      "r2_with_treatment": r2dz, "r2_with_yield": r2yz,
                      "adjusted_effect_t_ha": adj, "adj_ci_low": adj - Z * adj_se,
                      "adj_ci_high": adj + Z * adj_se})
bench = pd.DataFrame(bench)
bench.to_csv(TAB / "sensemakr_benchmarks.csv", index=False)
print(f"sensemakr done ({time.time() - t0:.0f}s)")

# ------------------------------------------------------------------ C. district differences
dist_rows = []
Xall = design_matrix(df)
keep_cols = [c for c in Xall.columns if not c.startswith(("Year_", "District_"))]
for dname, g in df.groupby("District"):
    g = g[g.groupby("Year").Treated.transform(lambda v: 0 < v.mean() < 1)]
    if g.Treated.nunique() < 2 or g.Year.nunique() < 3:
        continue  # too few seasons for a stable within-district fit
    Xg = Xall.loc[g.index, keep_cols]
    Xg = Xg.loc[:, Xg.std() > 0]
    fe = pd.get_dummies(g.Year, drop_first=True, dtype=float, prefix="Y")
    row = {"District": dname, "n": len(g), "seasons": g.Year.nunique()}
    for col, lab in [("logYield", "yield"), ("logEars", "ears"),
                     ("logYieldPerEar", "yield_per_ear")]:
        Xd = sm.add_constant(pd.concat([g[["Treated"]].astype(float), Xg, fe], axis=1))
        r = sm.OLS(g[col], Xd).fit(cov_type="cluster",
                                   cov_kwds={"groups": pd.factorize(g.ClusterBlockYear)[0]})
        row[f"{lab}_pct"] = pct(r.params["Treated"])
        row[f"{lab}_ci_low"] = pct(r.conf_int().loc["Treated", 0])
        row[f"{lab}_ci_high"] = pct(r.conf_int().loc["Treated", 1])
    dist_rows.append(row)
dist = pd.DataFrame(dist_rows).sort_values("yield_pct")
dist.to_csv(TAB / "district_negative_control.csv", index=False)
corr_ears = float(np.corrcoef(dist.yield_pct, dist.ears_pct)[0, 1])

# ------------------------------------------------------------------ figures
a = neg[(neg["sample"] == "all plots")]
order = [o[1] for o in OUTCOMES]
fig, ax = plt.subplots(figsize=(9, 4.8))
for j, (m, c, off) in enumerate([("District x season FE regression", GREEN, 0.15),
                                  ("Double ML", BLUE, -0.15)]):
    s = a[a.method == m].set_index("outcome").loc[order]
    y = np.arange(len(s))[::-1] + off
    ax.errorbar(s.pct_effect, y, xerr=[s.pct_effect - s.ci_low, s.ci_high - s.pct_effect],
                fmt="o", color=c, ecolor=c, capsize=2.5, label=m)
ax.axvline(0, color="#333", lw=0.8)
ax.set_yticks(np.arange(len(order))[::-1], order, fontsize=8.5)
for i, (_, _, role) in enumerate(OUTCOMES):
    if role == "negative control":
        ax.axhspan(len(order) - 1 - i - 0.45, len(order) - 1 - i + 0.45, color=RED, alpha=0.08)
ax.set_xlabel("Adjusted % difference, extra irrigation vs control (95% CI)")
ax.set_title("Negative-control test: the late irrigation 'raises' ear count,\n"
             "which it cannot cause -> hidden differences between plots")
ax.legend(frameon=False, fontsize=8, loc="lower right")
fig.tight_layout(); fig.savefig(FIG / "fig21_negative_control.png"); plt.close(fig)

# contour plot of adjusted estimate with benchmarks
r2d = np.linspace(0, 0.5, 120); r2y = np.linspace(0, 0.5, 120)
D, Yg = np.meshgrid(r2d, r2y)
adj = np.vectorize(lambda a_, b_: float(smk.adjusted_estimate(
    a_, b_, estimate=b_hat, se=se_hat, dof=dof)))(np.clip(D, 1e-6, 0.999), Yg)
fig, ax = plt.subplots(figsize=(7, 5.6))
cs = ax.contour(D, Yg, adj, levels=np.arange(-0.6, 1.2, 0.2), colors=GREY, linewidths=0.8)
ax.clabel(cs, fmt="%.1f", fontsize=7)
c0 = ax.contour(D, Yg, adj, levels=[0], colors=RED, linewidths=2)
cc = ax.contour(D, Yg, adj, levels=[ctrl_mean * get("Yield per ear").pct_effect / 100],
                colors=BLUE, linewidths=1.6, linestyles="--")
mk = {"Irrigations already given": "o", "Sowing day": "s",
      "Fertiliser practice (8 vars)": "^", "District x season (56 cells)": "D"}
for r in bench.itertuples():
    if r.r2_with_treatment <= 0.5 and r.r2_with_yield <= 0.5:
        ax.scatter(r.r2_with_treatment, r.r2_with_yield, marker=mk[r.benchmark], color="#333",
                   s=30, zorder=5)
        ax.annotate(f"{r.k_times_as_strong}x {r.benchmark.split(' (')[0]}",
                    (r.r2_with_treatment, r.r2_with_yield), fontsize=6.5,
                    xytext=(4, 3), textcoords="offset points")
ax.set_xlabel("Hidden factor: partial R2 with getting the extra irrigation")
ax.set_ylabel("Hidden factor: partial R2 with yield")
ax.set_title(f"How strong must a hidden factor be? (estimate {b_hat:.2f} t/ha)\n"
             "grey = adjusted effect; blue dashed = ear-calibrated value;\n"
             "red = zero (beyond this range)", fontsize=9.5)
fig.tight_layout(); fig.savefig(FIG / "fig22_sensitivity_contour.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4.2))
x = np.arange(len(dist))
ax.bar(x - 0.2, dist.yield_pct, 0.4, color=GREEN, label="Yield effect (%)")
ax.bar(x + 0.2, dist.ears_pct, 0.4, color=RED, alpha=0.8, label="Ear-count 'effect' (%) - impossible")
ax.set_xticks(x, dist.District, rotation=25, ha="right")
ax.axhline(0, color="#333", lw=0.8)
ax.set_ylabel("Adjusted % difference")
ax.set_title(f"By district: where yield gains are big, so is the impossible ear gain\n"
             f"(correlation {corr_ears:.2f}; districts with >= 3 seasons)")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(FIG / "fig23_district_negative_control.png"); plt.close(fig)

# ------------------------------------------------------------------ summary
das = df.ExtraIrrigationDAS.dropna()
L = ["# Agri-Vision - Sensitivity to Hidden Confounding", "",
     f"Extra irrigation timing: median {das.median():.0f} days after sowing "
     f"(IQR {das.quantile(.25):.0f}-{das.quantile(.75):.0f}; {(das >= 100).mean():.0%} at >= 100 DAS).", "",
     "## A. Negative-control outcomes (adjusted % differences)", "",
     neg.round(2).to_markdown(index=False), "",
     "### Calibrated effect (assumes the hidden factor acts through ear count / grain number)", "",
     cal.round(3).to_markdown(index=False), "",
     "## B. Formal sensitivity (Cinelli & Hazlett 2020) - district x season FE regression", "",
     f"- Estimate {b_hat:.3f} t/ha (SE {se_hat:.3f}, OLS); partial R2 of treatment with yield "
     f"{float(np.ravel(r2yd)[0]):.3f}.",
     f"- Robustness value RV = **{float(np.ravel(rv)[0]):.3f}**: a hidden factor explaining "
     f"{float(np.ravel(rv)[0]):.1%} of the remaining variation of both treatment and yield would "
     "reduce the effect to zero.",
     f"- RV (to lose 5% significance) = {float(np.ravel(rv_a)[0]):.3f}.",
     f"- RV to bring the estimate down to the ear-calibrated value ({q_cal:.0%} reduction) = "
     f"{float(np.ravel(rv_cal)[0]):.3f}.", "",
     "Benchmarks: a hidden factor k times as strong as a measured one.", "",
     bench.round(3).to_markdown(index=False), "",
     "## C. District differences vs the impossible ear effect", "",
     dist.round(1).to_markdown(index=False), "",
     f"- Correlation across districts between yield effect and ear 'effect': **{corr_ears:.2f}**.",
     ""]
(ROOT / "outputs" / "sensitivity_summary.md").write_text("\n".join(L), encoding="utf-8")
print("\n".join(L))
print(f"total {time.time() - t0:.0f}s")
