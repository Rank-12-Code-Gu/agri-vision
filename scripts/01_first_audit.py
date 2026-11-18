"""First audit of the CSISA eastern-India wheat irrigation trial data.

Run from the project root:
    .venv/Scripts/python scripts/01_first_audit.py
"""
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
CSV = RAW / "CSISA_IND_Irrigation_Trial_Data_2017-22_Final.csv"

pd.set_option("display.width", 200)

df = pd.read_csv(CSV, encoding="latin1")
df.columns = df.columns.str.strip()  # e.g. 'Village ' has a trailing space
df["SoilType"] = df["SoilType"].str.strip().str.capitalize()  # 'medium' vs 'Medium'

print("Rows, columns:", df.shape)

print("\n== Treatment balance ==")
print(df["Plot"].value_counts().to_string())
print("\nBy year:\n", pd.crosstab(df["Year"], df["Plot"]))
print("\nBy district:\n", pd.crosstab(df["District"], df["Plot"]))

print("\n== Pairing check (same year + village + GPS at 2 decimals, ~1 km) ==")
key = ["Year", "Village", "Latitude", "Longitude"]
arms = df.groupby(key)["Plot"].agg(lambda s: frozenset(s))
print("Locality groups:", len(arms))
print("Groups with both arms:", int((arms.apply(len) == 2).sum()))

print("\n== Unadjusted grain yield (t/ha) -- NOT a causal estimate ==")
print(df.groupby("Plot")["GrainYield"].describe().round(2).to_string())

print("\n== Raw difference by subgroup (hint of heterogeneity) ==")
for col in ["SowingWindow", "CropEstablishment", "IrrigationNumber", "SoilType", "LandType"]:
    t = df.groupby([col, "Plot"])["GrainYield"].agg(["mean", "count"]).unstack()
    t["raw_diff"] = t[("mean", "Treatment")] - t[("mean", "Control")]
    print(f"\n{col}:\n", t.round(2).to_string())
