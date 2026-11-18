"""Who benefits from the extra irrigation? Causal forest + validation + targeting.

Run from the project root:
    .venv/Scripts/python scripts/05_who_benefits.py
Writes models/cate_forest.joblib, figures 12-17, tables, outputs/who_benefits_summary.md.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.tree import DecisionTreeRegressor, export_text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agrivision import economics as eco  # noqa: E402
from agrivision import estimators as est  # noqa: E402
from agrivision import heterogeneity as het  # noqa: E402
from agrivision.data import design_matrix, load_clean  # noqa: E402

FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"
MOD = ROOT / "models"
for p in (FIG, TAB, MOD):
    p.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 10})
GREEN, GREY, RED = "#1b7f5a", "#8c8c8c", "#c0392b"
Z = 1.959963984540054
t0 = time.time()

df = load_clean()
levels = het.modifier_levels(df)
Xm = het.build_modifiers(df, levels)
W = het.build_controls(df)
groups = df.ClusterBlockYear

# ------------------------------------------------------------------ 1. full-data forest
cf = het.fit_forest(df, Xm, W, seed=0)
cate = cf.effect(Xm.to_numpy())
lb, ub = cf.effect_interval(Xm.to_numpy(), alpha=0.05)
ate = float(np.ravel(cf.ate_)[0])
ate_se = float(np.ravel(cf.ate_stderr_)[0])
print(f"forest fitted ({time.time() - t0:.0f}s); ATE {ate:.3f} +/- {ate_se:.3f}")

# ------------------------------------------------------------------ 2. DR scores
nu = est.cross_fit_nuisance(df, design_matrix(df), seed=0)
psi = het.dr_scores(df, nu)

# ------------------------------------------------------------------ 3. validation (out-of-fold)
oof = het.out_of_fold_cate(df, Xm, W, seed=0)
print(f"out-of-fold CATE done ({time.time() - t0:.0f}s)")

# BLP calibration test: psi = a + b * (oof - mean) ; b > 0 means heterogeneity is real
Xb = sm.add_constant(oof - oof.mean())
blp = sm.OLS(psi, Xb).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(groups)[0]})
b, b_se = float(blp.params[1]), float(blp.bse[1])
b_p = float(blp.pvalues[1])

# GATES: average DR effect within quintiles of predicted benefit
q = pd.qcut(oof, 5, labels=[f"Q{i}" for i in range(1, 6)])
gates = []
for lab in q.categories:
    m = (q == lab)
    mean, se = het.cluster_mean(psi[m], groups[m])
    gates.append({"group": lab, "pred_mean": oof[m].mean(), "dr_effect": mean, "se": se,
                  "ci_low": mean - Z * se, "ci_high": mean + Z * se, "n": int(m.sum())})
gates = pd.DataFrame(gates)
gates.to_csv(TAB / "gates_quintiles.csv", index=False)
top_minus_bottom = gates.dr_effect.iloc[-1] - gates.dr_effect.iloc[0]
sel = (q == "Q5") | (q == "Q1")
d_psi = np.where(q[sel] == "Q5", psi[sel], 0) / (q == "Q5").mean() \
    - np.where(q[sel] == "Q1", psi[sel], 0) / (q == "Q1").mean()
# simple cluster-robust SE of the Q5-Q1 gap via regression on a Q5 dummy
dq = pd.DataFrame({"psi": psi[sel], "q5": (q[sel] == "Q5").astype(float)})
gap_fit = sm.OLS(dq.psi, sm.add_constant(dq.q5)).fit(
    cov_type="cluster", cov_kwds={"groups": pd.factorize(groups[sel])[0]})
gap_se, gap_p = float(gap_fit.bse["q5"]), float(gap_fit.pvalues["q5"])

# ------------------------------------------------------------------ 4. subgroup effects
labels = {
    "BaseIrrigations": "Irrigations already given by farmer",
    "SowingWindow": "Sowing window",
    "CropEstablishment": "Tillage (ZT = zero tillage, CT = conventional)",
    "SoilType": "Soil type", "LandType": "Land type", "District": "District",
}
sub = []
for col, title in labels.items():
    for lev, idx in df.groupby(col).groups.items():
        idx = np.asarray(idx)
        if len(idx) < 30:
            continue
        mean, se = het.cluster_mean(psi[idx], groups.iloc[idx])
        sub.append({"factor": title, "level": str(lev), "n": len(idx),
                    "n_treated": int(df.Treated.iloc[idx].sum()),
                    "dr_effect": mean, "ci_low": mean - Z * se, "ci_high": mean + Z * se,
                    "forest_mean": cate[idx].mean()})
sub = pd.DataFrame(sub)
sub.to_csv(TAB / "subgroup_effects.csv", index=False)

# ------------------------------------------------------------------ 5. importance
imp = pd.Series(cf.feature_importances_, index=Xm.columns)
imp_grp = imp.groupby(lambda c: c.split("=")[0]).sum().sort_values(ascending=False)
imp_grp.to_csv(TAB / "cate_importance.csv", header=["importance"])

# ------------------------------------------------------------------ 6. economics
be = eco.break_even_gain_t_per_ha()
net = eco.net_benefit_rs_per_ha(cate)
share_pay = float((lb > be).mean())
share_point_pay = float((cate > be).mean())

# ------------------------------------------------------------------ 7. priority curve
order = np.argsort(-oof)
fr = np.linspace(0, 1, 101)
n = len(df)
gain_model = [psi[order[: int(round(f * n))]].sum() / n for f in fr]
gain_random = [f * psi.mean() for f in fr]
budget = []
for f in (0.25, 0.5, 0.75):
    k = int(round(f * n))
    budget.append({"share_irrigated": f, "gain_targeted": psi[order[:k]].sum() / n,
                   "gain_random": f * psi.mean(),
                   "share_of_full_gain_captured": psi[order[:k]].sum() / psi.sum()})
budget = pd.DataFrame(budget)
budget.to_csv(TAB / "priority_budget.csv", index=False)

# ------------------------------------------------------------------ 8. simple rule
readable = df[["SowingDay", "BaseIrrigations", "ZeroTillage"]].astype(float).copy()
for c in ["SoilType", "LandType"]:
    for lev in levels[c]:
        readable[f"{c}={lev}"] = (df[c] == lev).astype(float)
tree = DecisionTreeRegressor(max_depth=2, min_samples_leaf=150, random_state=0)
tree.fit(readable, cate)
rule_text = export_text(tree, feature_names=list(readable.columns), decimals=2)

# ------------------------------------------------------------------ 9. save model
overlap = (df.groupby(["District", "Year"]).Treated.mean().between(0.0001, 0.9999)
           .groupby("District").sum().astype(int).to_dict())
joblib.dump({
    "forest": cf, "levels": levels, "modifier_columns": list(Xm.columns),
    "ate": ate, "ate_se": ate_se, "sowing_day_range": (int(df.SowingDay.min()),
                                                       int(df.SowingDay.max())),
    "district_seasons_with_both_arms": overlap,
    "n_by_district": df.District.value_counts().to_dict(),
    "n_by_base": df.BaseIrrigations.value_counts().to_dict(),
    "subgroups": sub, "gates": gates, "importance": imp_grp,
}, MOD / "cate_forest.joblib", compress=3)
print(f"model saved ({time.time() - t0:.0f}s)")

# ------------------------------------------------------------------ figures
fig, ax = plt.subplots(figsize=(7, 3.6))
ax.hist(cate, bins=40, color=GREEN, alpha=0.85)
ax.axvline(be, color=RED, ls="--", lw=1.5, label=f"Break-even gain {be:.2f} t/ha")
ax.axvline(ate, color="#333", lw=1.2, label=f"Average {ate:.2f} t/ha")
ax.set_xlabel("Predicted yield gain from extra irrigation (t/ha)")
ax.set_ylabel("Plots")
ax.set_title("Not every farm gains the same: predicted gain per plot")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(FIG / "fig12_cate_distribution.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 3.8))
x = np.arange(5)
ax.bar(x, gates.dr_effect, color=GREEN, alpha=0.85, label="Measured (doubly robust)")
ax.errorbar(x, gates.dr_effect, yerr=[gates.dr_effect - gates.ci_low,
                                       gates.ci_high - gates.dr_effect],
            fmt="none", ecolor="#333", capsize=4)
ax.plot(x, gates.pred_mean, "o-", color=RED, label="Predicted by forest")
ax.set_xticks(x, ["Q1\nlowest", "Q2", "Q3", "Q4", "Q5\nhighest"])
ax.set_ylabel("Yield gain (t/ha)")
ax.set_title("Validation: farms predicted to benefit more really do\n"
             "(groups predicted out-of-fold)")
ax.legend(frameon=False, loc="upper left")
fig.tight_layout(); fig.savefig(FIG / "fig13_gates_validation.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 8.5))
yy, ticks, pos = [], [], 0
for fac, g in sub.groupby("factor", sort=False):
    ax.text(-0.05, pos, fac, transform=ax.get_yaxis_transform(), ha="right",
            va="center", weight="bold", fontsize=8.5)
    pos -= 1
    for r in g.itertuples():
        ax.errorbar(r.dr_effect, pos, xerr=[[r.dr_effect - r.ci_low], [r.ci_high - r.dr_effect]],
                    fmt="o", color=GREEN, ecolor="#555", capsize=2.5)
        ticks.append((pos, f"{r.level}  (n={r.n})"))
        pos -= 1
    pos -= 0.4
ax.set_yticks([t[0] for t in ticks], [t[1] for t in ticks], fontsize=8)
ax.axvline(ate, color="#333", lw=1, ls=":", label=f"Overall {ate:.2f}")
ax.axvline(be, color=RED, lw=1.2, ls="--", label=f"Break-even {be:.2f}")
ax.set_xlabel("Yield gain from extra irrigation (t/ha), 95% CI")
ax.set_title("Who benefits? Effect by farm group")
ax.legend(frameon=False, loc="lower right", fontsize=8)
fig.tight_layout(); fig.savefig(FIG / "fig14_subgroup_effects.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(6.5, 3.4))
ax.barh(imp_grp.index[::-1], imp_grp.values[::-1], color=GREEN)
ax.set_xlabel("Share of forest splits (importance)")
ax.set_title("What drives differences in benefit?")
fig.tight_layout(); fig.savefig(FIG / "fig15_cate_importance.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(fr * 100, gain_model, color=GREEN, lw=2, label="Agri-Vision priority order")
ax.plot(fr * 100, gain_random, color=GREY, ls="--", label="Random order")
ax.set_xlabel("% of farms that can get the extra irrigation (water / diesel budget)")
ax.set_ylabel("Average yield gain per farm (t/ha)")
ax.set_title("If water is limited, who should get it first?")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(FIG / "fig16_priority_curve.png"); plt.close(fig)

# Effect vs sowing day for each base-irrigation level (typical other values)
typ = df.mode(numeric_only=False).iloc[0]
grid = np.arange(df.SowingDay.min(), df.SowingDay.max() + 1, 2)
fig, ax = plt.subplots(figsize=(7, 4))
for b_ in [1, 2, 3, 4]:
    prof = pd.DataFrame({c: [typ[c]] * len(grid) for c in
                         het.MODIFIER_NUMERIC + het.MODIFIER_CATEGORICAL})
    prof["SowingDay"] = grid
    prof["BaseIrrigations"] = b_
    Xp = het.build_modifiers(prof, levels).to_numpy()
    eff = cf.effect(Xp)
    lo, hi = cf.effect_interval(Xp, alpha=0.05)
    ax.plot(grid, eff, label=f"{b_} irrigation(s) already given")
    ax.fill_between(grid, lo, hi, alpha=0.12)
ax.axhline(be, color=RED, ls="--", lw=1, label="Break-even")
ax.set_xlabel("Sowing day (day of year; 305 = 1 Nov, 335 = 1 Dec)")
ax.set_ylabel("Predicted gain (t/ha)")
ax.set_title(f"Predicted gain by sowing date - typical farm\n"
             f"({typ.District}, {typ.SoilType} soil, {typ.VarietyGrp}, "
             f"{'ZT' if typ.ZeroTillage else 'CT'})")
ax.legend(frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(FIG / "fig17_gain_by_sowing_date.png"); plt.close(fig)

# ------------------------------------------------------------------ summary
L = ["# Agri-Vision - Who Benefits? (causal forest)", "",
     "Model: CausalForestDML (econml), 2,000 honest trees, gradient-boosting nuisance "
     "models, 5-fold cross-fitting grouped by block x season.",
     f"Effect modifiers: {', '.join(het.MODIFIER_NUMERIC + het.MODIFIER_CATEGORICAL)}.",
     "Controls only: season, fertiliser, seed rate, residue, GPS, weeding, previous crop.", "",
     "## Average effect", "",
     f"- Forest ATE: **{ate:+.3f} t/ha** (95% CI {ate - Z * ate_se:+.3f} to {ate + Z * ate_se:+.3f}).",
     f"- Predicted plot-level gain ranges {cate.min():.2f} to {cate.max():.2f} t/ha "
     f"(10th-90th percentile {np.percentile(cate, 10):.2f} to {np.percentile(cate, 90):.2f}).", "",
     "## Is the heterogeneity real? (out-of-fold validation)", "",
     f"- Calibration slope (BLP): **{b:.2f}** (SE {b_se:.2f}, p = {b_p:.3g}). "
     "1 = predictions perfectly calibrated; 0 = no real heterogeneity detected.",
     f"- Top-quintile minus bottom-quintile measured gain: **{top_minus_bottom:+.3f} t/ha** "
     f"(SE {gap_se:.3f}, p = {gap_p:.3g}).", "",
     gates.round(3).to_markdown(index=False), "",
     "## Effect by farm group (doubly robust, cluster-robust 95% CI)", "",
     sub.round(3).to_markdown(index=False), "",
     "## What drives the differences (forest importance)", "",
     imp_grp.round(3).to_frame("importance").to_markdown(), "",
     "## Economics (assumptions in src/agrivision/economics.py - verify)", "",
     f"- Wheat price Rs {eco.WHEAT_PRICE_RS_PER_QUINTAL}/quintal; irrigation cost "
     f"Rs {eco.IRRIGATION_COST_RS_PER_HA}/ha -> break-even gain **{be:.3f} t/ha**.",
     f"- Plots whose predicted gain exceeds break-even: {share_point_pay:.1%}; "
     f"whose 95% lower bound exceeds it: {share_pay:.1%}.",
     f"- Median net benefit: Rs {np.median(net):,.0f}/ha.", "",
     "## If water/diesel is limited: priority targeting", "",
     budget.round(3).to_markdown(index=False), "",
     "## Simple readable rule (depth-2 tree fitted to forest predictions)", "",
     "```", rule_text, "```", ""]
(ROOT / "outputs" / "who_benefits_summary.md").write_text("\n".join(L), encoding="utf-8")
print("\n".join(L))
print(f"total {time.time() - t0:.0f}s")
