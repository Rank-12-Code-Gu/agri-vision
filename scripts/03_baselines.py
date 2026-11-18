"""Baseline estimates of the extra-irrigation effect on wheat grain yield.

Run from the project root:
    .venv/Scripts/python scripts/03_baselines.py
Writes outputs/tables/baselines.csv, figures 06-08 and outputs/baselines_summary.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agrivision import estimators as est  # noqa: E402
from agrivision.data import design_matrix, load_clean, smd  # noqa: E402

FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"
FIG.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 10})
C_CTRL, C_TRT = "#8c8c8c", "#1b7f5a"

df = load_clean()
X = design_matrix(df)
t = df.Treated.to_numpy()

# ------------------------------------------------------------------ main estimates
nu = est.cross_fit_nuisance(df, X, seed=0)
results = [
    est.naive_difference(df),
    est.ols_adjusted(df, X),
    est.ols_district_year_fe(df, X),
    est.matched_set_fe(df, X),
    est.ipw(df, nu),
    est.aipw(df, nu),
    est.dml_plr(df, nu),
]
res = pd.DataFrame(results)
res.to_csv(TAB / "baselines.csv", index=False)

# ------------------------------------------------------------------ stability of ML estimators
seeds = range(1, 11)
stab = []
for s in seeds:
    nu_s = est.cross_fit_nuisance(df, X, seed=s)
    for f in (est.ipw, est.aipw, est.dml_plr):
        r = f(df, nu_s)
        stab.append({"seed": s, "method": r["method"], "estimate": r["estimate"]})
stab = pd.DataFrame(stab)
stab_sum = stab.groupby("method").estimate.agg(["mean", "std", "min", "max"])
stab_sum.to_csv(TAB / "ml_seed_stability.csv")

# ------------------------------------------------------------------ robustness checks
rob = []
keep = df.FlagControlWithAddlDate == 0
d2 = df[keep].reset_index(drop=True)
X2 = design_matrix(d2)
nu2 = est.cross_fit_nuisance(d2, X2, seed=0)
rob.append({"check": "Drop 36 flagged Bhojpur 2021-22 controls",
            **{k: v for k, v in est.aipw(d2, nu2).items() if k in ("estimate", "se", "n")}})
nu_logit = est.cross_fit_nuisance(df, X, seed=0, learner="logit")
rob.append({"check": "AIPW with logistic propensity",
            **{k: v for k, v in est.aipw(df, nu_logit).items() if k in ("estimate", "se", "n")}})
rob.append({"check": "AIPW, propensity clipped to [0.10, 0.90]",
            **{k: v for k, v in est.aipw(df, nu, trim=(0.1, 0.9)).items()
               if k in ("estimate", "se", "n")}})
for yr in sorted(df.Year.unique()):
    d3 = df[df.Year != yr].reset_index(drop=True)
    X3 = design_matrix(d3)
    r = est.aipw(d3, est.cross_fit_nuisance(d3, X3, seed=0))
    rob.append({"check": f"AIPW leaving out season {yr}",
                **{k: v for k, v in r.items() if k in ("estimate", "se", "n")}})
cell_share = df.groupby("DistrictYear").Treated.transform("mean")
for lo, hi, label in [(0.4, 0.6, "only district-seasons with 40-60% treated"),
                      (0.0001, 0.9999, "drop district-seasons that are 0% or 100% treated")]:
    d4 = df[(cell_share >= lo) & (cell_share <= hi)].reset_index(drop=True)
    X4 = design_matrix(d4)
    r = est.aipw(d4, est.cross_fit_nuisance(d4, X4, seed=0))
    rob.append({"check": f"AIPW {label}",
                **{k: v for k, v in r.items() if k in ("estimate", "se", "n")}})
    r = est.ols_district_year_fe(d4, X4)
    rob.append({"check": f"District x season FE {label}",
                **{k: v for k, v in r.items() if k in ("estimate", "se", "n")}})
cells = df.groupby("DistrictYear").Treated.mean()
n_pure = int(((cells == 0) | (cells == 1)).sum())
n_pure_plots = int(df[cell_share.isin([0, 1])].shape[0])
rob = pd.DataFrame(rob)
rob.to_csv(TAB / "robustness.csv", index=False)

# ------------------------------------------------------------------ propensity diagnostics
auc = roc_auc_score(t, nu["e"])
e = nu["e"]
outside = float(((e < 0.05) | (e > 0.95)).mean())

fig, ax = plt.subplots(figsize=(7, 3.6))
bins = np.linspace(0, 1, 31)
ax.hist(e[t == 0], bins=bins, alpha=0.65, color=C_CTRL, label="Control", density=True)
ax.hist(e[t == 1], bins=bins, alpha=0.65, color=C_TRT, label="Extra irrigation", density=True)
ax.set_xlabel("Estimated probability of receiving extra irrigation (propensity)")
ax.set_ylabel("Density")
ax.set_title(f"Overlap check - propensity AUC = {auc:.2f}")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(FIG / "fig06_propensity_overlap.png")
plt.close(fig)

# Love plot: balance before and after weighting
ec = np.clip(e, 0.05, 0.95)
w = np.where(t == 1, 1 / ec, 1 / (1 - ec))
cols = [c for c in X.columns]
lp = pd.DataFrame({
    "raw": [smd(X[c].to_numpy(), t) for c in cols],
    "weighted": [smd(X[c].to_numpy(), t, w) for c in cols],
}, index=cols)
lp.to_csv(TAB / "covariate_balance_weighted.csv")
top = lp.reindex(lp.raw.abs().sort_values(ascending=False).index).head(20)[::-1]
fig, ax = plt.subplots(figsize=(7, 6))
yy = np.arange(len(top))
ax.scatter(top.raw.abs(), yy, color="#c0392b", label="Before weighting", zorder=3)
ax.scatter(top.weighted.abs(), yy, color=C_TRT, label="After weighting", zorder=3)
for i, (a, b) in enumerate(zip(top.raw.abs(), top.weighted.abs())):
    ax.plot([a, b], [i, i], color="#bbb", lw=1)
ax.axvline(0.1, ls="--", color="#333", lw=1)
ax.set_yticks(yy, top.index, fontsize=8)
ax.set_xlabel("|Standardised mean difference|  (dashed line = 0.10)")
ax.set_title("Covariate balance: 20 most imbalanced variables")
ax.legend(frameon=False, loc="lower right")
fig.tight_layout()
fig.savefig(FIG / "fig07_balance_love_plot.png")
plt.close(fig)

# Forest plot of estimates
fig, ax = plt.subplots(figsize=(8, 4.2))
yy = np.arange(len(res))[::-1]
ax.errorbar(res.estimate, yy, xerr=[res.estimate - res.ci_low, res.ci_high - res.estimate],
            fmt="o", color=C_TRT, ecolor="#555", capsize=3)
ax.axvline(0, color="#333", lw=0.8)
ax.set_yticks(yy, res.method)
for y_, r in zip(yy, res.itertuples()):
    ax.text(r.ci_high + 0.02, y_, f"{r.estimate:+.2f}", va="center", fontsize=8.5)
ax.set_xlabel("Estimated yield gain from extra irrigation (t/ha), 95% CI")
ax.set_title("Same data, different methods, different answers")
fig.tight_layout()
fig.savefig(FIG / "fig08_baseline_forest.png")
plt.close(fig)

# ------------------------------------------------------------------ summary
ctrl_mean = df.loc[t == 0, "GrainYield"].mean()
L = ["# Agri-Vision - Baseline Effect Estimates", "",
     "Outcome: grain yield (t/ha). Treatment: one extra irrigation at grain filling.",
     "Standard errors clustered by block x season. Only pre-treatment covariates used.", "",
     "## Estimates", ""]
show = res.copy()
show["% of control mean"] = (show.estimate / ctrl_mean * 100).round(1)
L.append(show[["method", "estimate", "se", "ci_low", "ci_high", "% of control mean", "n", "note"]]
         .round(3).to_markdown(index=False))
L += ["", f"Spread across methods: {res.estimate.min():+.3f} to {res.estimate.max():+.3f} t/ha "
      f"(range {res.estimate.max() - res.estimate.min():.3f}).", "",
      "## Propensity / overlap diagnostics", "",
      f"- Cross-fitted propensity AUC: **{auc:.3f}** (0.5 = assignment unpredictable "
      "= like randomisation; near 1 = groups very different).",
      f"- Plots with propensity outside [0.05, 0.95]: {outside:.1%}.",
      f"- District x season cells that are 0% or 100% treated (no comparison group "
      f"inside the cell): **{n_pure} of {len(cells)}**, holding {n_pure_plots} plots.",
      f"- Covariates with |SMD| > 0.10: {int((lp.raw.abs() > 0.1).sum())} before weighting, "
      f"{int((lp.weighted.abs() > 0.1).sum())} after weighting (of {len(lp)}).", "",
      "## Stability of ML estimators over 10 random seeds", "",
      stab_sum.round(3).to_markdown(), "",
      "## Robustness checks (AIPW)", "", rob.round(3).to_markdown(index=False), ""]
(ROOT / "outputs" / "baselines_summary.md").write_text("\n".join(L), encoding="utf-8")
print("\n".join(L))
