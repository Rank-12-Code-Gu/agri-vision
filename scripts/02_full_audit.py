"""Full data audit: balance, design, missingness, quality checks, charts.

Run from the project root:
    .venv/Scripts/python scripts/02_full_audit.py
Writes figures to outputs/figures and a summary to outputs/audit_summary.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agrivision.data import (  # noqa: E402
    CLEANING_LOG, FLAG_COVARIATES, NUMERIC_COVARIATES, load_clean, load_raw, smd,
)

FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"
FIG.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

C_CTRL, C_TRT = "#8c8c8c", "#1b7f5a"
plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 10})

raw = load_raw()
df = load_clean()
lines: list[str] = ["# Agri-Vision - Data Audit Summary", ""]
add = lines.append

# ---------------------------------------------------------------- overview
n_c, n_t = int((df.Treated == 0).sum()), int((df.Treated == 1).sum())
add("## 1. Overview")
add(f"- Plots: **{len(df)}** (control {n_c}, treatment {n_t}; "
    f"treated share {n_t / len(df):.1%})")
add(f"- Seasons: {df.Year.nunique()} ({', '.join(sorted(df.Year.unique()))})")
add(f"- Districts: {df.District.nunique()}; blocks: {df.Block.nunique()}; "
    f"villages: {df.Village.nunique()}")
add(f"- Exact duplicate rows: {int(raw.duplicated().sum())}")
add("")

# ---------------------------------------------------------------- imbalance
add("## 2. Treatment imbalance")
by_year = pd.crosstab(df.Year, df.Treated).rename(columns={0: "Control", 1: "Treatment"})
by_year["TreatedShare"] = (by_year.Treatment / by_year.sum(axis=1)).round(3)
by_dist = pd.crosstab(df.District, df.Treated).rename(columns={0: "Control", 1: "Treatment"})
by_dist["TreatedShare"] = (by_dist.Treatment / by_dist.sum(axis=1)).round(3)
by_year.to_csv(TAB / "balance_by_year.csv")
by_dist.to_csv(TAB / "balance_by_district.csv")
add("By season:\n")
add(by_year.to_markdown())
add("\nBy district:\n")
add(by_dist.sort_values("TreatedShare").to_markdown())
dy = pd.crosstab(df.District, df.Year)
add(f"\n- Treated share ranges from {by_dist.TreatedShare.min():.0%} to "
    f"{by_dist.TreatedShare.max():.0%} across districts and "
    f"{by_year.TreatedShare.min():.0%} to {by_year.TreatedShare.max():.0%} across seasons.")
add(f"- District x season cells with no plots: {int((dy == 0).sum().sum())} of {dy.size}.")
add("")

# Figure 1: treated share heatmap with counts
share = df.pivot_table(index="District", columns="Year", values="Treated", aggfunc="mean")
count = df.pivot_table(index="District", columns="Year", values="Treated", aggfunc="size")
order = share.mean(axis=1).sort_values().index
share, count = share.loc[order], count.loc[order]
fig, ax = plt.subplots(figsize=(8, 5))
im = ax.imshow(share.values, cmap="BrBG", vmin=0, vmax=1, aspect="auto")
for i in range(share.shape[0]):
    for j in range(share.shape[1]):
        n = count.values[i, j]
        if not np.isnan(n):
            ax.text(j, i, f"{share.values[i, j]:.0%}\nn={int(n)}", ha="center",
                    va="center", fontsize=7.5)
        else:
            ax.text(j, i, "-", ha="center", va="center", color="#999")
ax.set_xticks(range(share.shape[1]), share.columns)
ax.set_yticks(range(share.shape[0]), share.index)
ax.set_title("Share of plots receiving the extra irrigation\n(50% = balanced)")
fig.colorbar(im, ax=ax, label="Treated share", shrink=0.8)
fig.tight_layout()
fig.savefig(FIG / "fig01_treatment_share_heatmap.png")
plt.close(fig)

# ---------------------------------------------------------------- design
add("## 3. Study design: is it a paired trial?")
sets = df.groupby("MatchSet").Treated.agg(["size", "sum"])
both = sets[(sets["sum"] > 0) & (sets["sum"] < sets["size"])]
n_in_both = int(both["size"].sum())
add("Plots were grouped into 'match sets' = same season, block, village, sowing date, "
    "variety and tillage (the closest available proxy for 'same farmer', since "
    "farmer IDs are anonymised).")
add(f"- Match sets: {len(sets)}; sets containing both arms: **{len(both)}** "
    f"({n_in_both} plots, {n_in_both / len(df):.0%} of data).")
add(f"- Plots with no comparable plot of the other arm: "
    f"{len(df) - n_in_both} ({(len(df) - n_in_both) / len(df):.0%}).")
add("- Conclusion: the data behave mostly like **unpaired, voluntarily assigned** "
    "plots, so simple averages can be confounded by place, season and practice.")
add("")

# ---------------------------------------------------------------- data quality
add("## 4. Data-quality checks and cleaning decisions")
for msg in CLEANING_LOG:
    add(f"- {msg}")
date_bad = df.loc[df.FlagControlWithAddlDate == 1, "DateofAdditionalIrrigation"]
month = pd.to_numeric(date_bad.str.split(".").str[1], errors="coerce")
add(f"- Of the flagged control dates, {int((month > 5).sum())} have an impossible "
    "month for a wheat season (e.g. '2022.10.03'), suggesting day/month swaps.")
add(f"- Grain yield range {df.GrainYield.min()}-{df.GrainYield.max()} t/ha; "
    f"grain > biomass in {int((df.GrainYield > df.BiomassYield).sum())} plots.")
q1, q3 = df.GrainYield.quantile([0.25, 0.75])
iqr = q3 - q1
out = df[(df.GrainYield < q1 - 3 * iqr) | (df.GrainYield > q3 + 3 * iqr)]
add(f"- Extreme yield outliers (beyond 3x IQR): {len(out)}.")
add("")

# Missingness (raw)
miss = raw.isna().mean().sort_values(ascending=False)
miss = miss[miss > 0]
add("Missing values in the raw file (share of rows):\n")
add(miss.round(3).rename("missing_share").to_markdown())
add("\nPost-treatment variables (lodging, biomass, test weight, tillers, grains, "
    "harvest date) are **excluded** from adjustment, because the extra irrigation "
    "can change them.")
add("")

fig, ax = plt.subplots(figsize=(7, 3.6))
ax.barh(miss.index[::-1], miss.values[::-1], color="#c98b2b")
ax.set_xlabel("Share of rows missing")
ax.set_xlim(0, 1)
ax.set_title("Missing values in the raw dataset")
fig.tight_layout()
fig.savefig(FIG / "fig02_missingness.png")
plt.close(fig)

# ---------------------------------------------------------------- covariate balance
add("## 5. Are treatment and control plots comparable before treatment?")
add("Standardised mean difference (SMD): |SMD| > 0.10 means the groups differ.\n")
rows = []
t = df["Treated"].to_numpy()
for col in NUMERIC_COVARIATES + FLAG_COVARIATES:
    rows.append((col, smd(df[col].astype(float).to_numpy(), t)))
for cat in ["Year", "District", "LandType", "SoilType", "VarietyGrp"]:
    for lev in sorted(df[cat].unique()):
        rows.append((f"{cat}={lev}", smd((df[cat] == lev).astype(float).to_numpy(), t)))
bal = pd.DataFrame(rows, columns=["covariate", "SMD_raw"]).set_index("covariate")
bal.to_csv(TAB / "covariate_balance_raw.csv")
big = bal[bal.SMD_raw.abs() > 0.1].sort_values("SMD_raw", key=abs, ascending=False)
add(f"- Covariates with |SMD| > 0.10: **{len(big)} of {len(bal)}**.\n")
add(big.round(3).to_markdown())
add("")

# ---------------------------------------------------------------- outcome
add("## 6. Outcome: grain yield (t/ha), unadjusted")
desc = df.groupby(df.Treated.map({0: "Control", 1: "Treatment"})).GrainYield.describe()
add(desc.round(2).to_markdown())
raw_diff = df.loc[df.Treated == 1, "GrainYield"].mean() - df.loc[df.Treated == 0, "GrainYield"].mean()
add(f"\n- Raw difference: **{raw_diff:+.3f} t/ha** "
    f"({raw_diff / df.loc[df.Treated == 0, 'GrainYield'].mean():+.1%}). "
    "This is NOT a causal estimate; see baselines.")
add("")

fig, ax = plt.subplots(figsize=(7, 3.8))
bins = np.arange(1.5, 7.01, 0.25)
ax.hist(df.loc[df.Treated == 0, "GrainYield"], bins=bins, alpha=0.65, color=C_CTRL,
        label=f"Control (n={n_c})", density=True)
ax.hist(df.loc[df.Treated == 1, "GrainYield"], bins=bins, alpha=0.65, color=C_TRT,
        label=f"Extra irrigation (n={n_t})", density=True)
ax.set_xlabel("Grain yield (t/ha)")
ax.set_ylabel("Density")
ax.set_title("Grain yield by arm (unadjusted)")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(FIG / "fig03_yield_distribution.png")
plt.close(fig)

# Raw diff by season (does the gap vary?)
gap = df.groupby(["Year", "Treated"]).GrainYield.mean().unstack()
gap["diff"] = gap[1] - gap[0]
fig, ax = plt.subplots(figsize=(7, 3.4))
ax.bar(gap.index, gap["diff"], color=C_TRT)
ax.axhline(raw_diff, ls="--", color="#333", lw=1, label=f"Pooled {raw_diff:+.2f}")
ax.set_ylabel("Treatment - control (t/ha)")
ax.set_title("Raw yield gap by season (unadjusted)")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(FIG / "fig04_raw_gap_by_season.png")
plt.close(fig)

# Map
fig, ax = plt.subplots(figsize=(7, 4.6))
jit = np.random.default_rng(0).normal(0, 0.01, size=(len(df), 2))
for arm, c, lab in [(0, C_CTRL, "Control"), (1, C_TRT, "Extra irrigation")]:
    m = df.Treated == arm
    ax.scatter(df.Longitude[m] + jit[m.to_numpy(), 0], df.Latitude[m] + jit[m.to_numpy(), 1],
               s=6, alpha=0.5, color=c, label=lab)
for d, g in df.groupby("District"):
    ax.annotate(d, (g.Longitude.mean(), g.Latitude.mean()), fontsize=7.5,
                ha="center", weight="bold")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_title("Trial locations (GPS truncated to ~1 km)")
ax.legend(frameon=False, markerscale=3)
fig.tight_layout()
fig.savefig(FIG / "fig05_trial_map.png")
plt.close(fig)

(ROOT / "outputs" / "audit_summary.md").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
