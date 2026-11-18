"""Build the models used by the Agri-Vision dashboard (app/app.py).

Three causal forests estimate the % yield effect of the extra irrigation for a farm
profile, each on a different outcome (see outputs/sensitivity_findings.md):
  * naive        : log(grain yield)            - what the raw trial data say
  * corrected    : log(yield per ear)          - impossible ear-count channel removed
  * conservative : log(yield per grain)        - ear + grain-number channels removed
A gradient-boosting model predicts the profile's yield WITHOUT the extra irrigation,
so % effects can be turned into t/ha and rupees.

Run from the project root:
    .venv/Scripts/python scripts/08_build_advisor.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agrivision import heterogeneity as het  # noqa: E402
from agrivision.data import load_clean  # noqa: E402

t0 = time.time()
df = load_clean()
df["logYield"] = np.log(df.GrainYield)
df["logYieldPerEar"] = df.logYield - np.log(df.TillersCount)
df["logYieldPerGrain"] = df.logYieldPerEar - np.log(df.GrainsCount)

levels = het.modifier_levels(df)
Xm = het.build_modifiers(df, levels)
W = het.build_controls(df)

forests = {}
for key, col in [("naive", "logYield"), ("corrected", "logYieldPerEar"),
                 ("conservative", "logYieldPerGrain")]:
    d = df.copy()
    d["GrainYield"] = d[col]
    forests[key] = het.fit_forest(d, Xm, W, seed=0)
    print(f"forest {key} fitted ({time.time() - t0:.0f}s)")

# Baseline (no extra irrigation) yield model on control plots, same modifiers.
ctrl = df.Treated == 0
base_model = HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, max_iter=300,
                                           random_state=0)
base_model.fit(Xm[ctrl], df.GrainYield[ctrl])

# District summary (forest averages over that district's real plots).
rows = []
both = df.groupby(["District", "Year"]).Treated.mean().between(0.0001, 0.9999)
for dname, g in df.groupby("District"):
    Xg = Xm.loc[g.index].to_numpy()
    base = base_model.predict(Xg)
    r = {"District": dname, "State": g.State.iloc[0], "plots": len(g),
         "seasons": g.Year.nunique(), "seasons_with_both_arms": int(both[dname].sum()),
         "lat": g.Latitude.mean(), "lon": g.Longitude.mean(),
         "baseline_yield": base.mean()}
    for key, cf in forests.items():
        pct = np.expm1(cf.effect(Xg))
        r[f"{key}_pct"] = 100 * pct.mean()
        r[f"{key}_t_ha"] = (base * pct).mean()
    rows.append(r)
districts = pd.DataFrame(rows)


def evidence(s):
    if s >= 5:
        return "Strong"
    if s >= 3:
        return "Moderate"
    return "Weak"


districts["evidence"] = districts.seasons_with_both_arms.map(evidence)

bundle = {
    "forests": forests, "base_model": base_model, "levels": levels,
    "modifier_numeric": het.MODIFIER_NUMERIC, "districts": districts,
    "sowing_day_range": (int(df.SowingDay.min()), int(df.SowingDay.max())),
    "typical": {c: df[c].mode().iloc[0] for c in ["SoilType", "LandType", "VarietyGrp"]},
    "n_plots": len(df), "seasons": sorted(df.Year.unique()),
    "built": time.strftime("%Y-%m-%d"),
}
out = ROOT / "models" / "advisor.joblib"
out.parent.mkdir(exist_ok=True)
joblib.dump(bundle, out, compress=3)
districts.round(3).to_csv(ROOT / "outputs" / "tables" / "advisor_district_table.csv", index=False)
print(districts.round(2).to_string())
print(f"saved {out} ({out.stat().st_size / 1e6:.1f} MB, {time.time() - t0:.0f}s)")
