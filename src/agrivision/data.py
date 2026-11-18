"""Load and clean the CSISA eastern-India wheat irrigation trial data.

Every cleaning decision is listed in CLEANING_LOG so it can be reported.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_CSV = ROOT / "data" / "raw" / "CSISA_IND_Irrigation_Trial_Data_2017-22_Final.csv"

IRRIGATION_DAY_COLS = [
    "FirstIrrigationDay", "SecondIrrigationDay", "ThirdIrrigationDay",
    "FourthIrrigationDay", "FifthIrrigationDay",
]

# Variables measured AFTER the treatment could be affected by it, so they must
# never be used as adjustment covariates (doing so would bias the estimate).
POST_TREATMENT = [
    "CropLodging", "HarvestDate", "BiomassYield", "TestWeight", "TillersCount",
    "GrainsCount", "DateofAdditionalIrrigation",
]

# Pre-treatment covariates used for adjustment.
NUMERIC_COVARIATES = [
    "SowingDay", "SeedRate", "PrevCropResidue", "BaseIrrigations",
    "FirstIrrigationDay", "BasalDAP_f", "BasalMOP", "Split1Urea", "Split2Urea",
    "Split3Urea_f", "Latitude", "Longitude",
]
FLAG_COVARIATES = ["UsedDAP", "UsedNPK", "UsedZn", "ManualWeedingYes", "ZeroTillage"]
CATEGORICAL_COVARIATES = [
    "Year", "District", "LandType", "SoilType", "PreviousCrop", "VarietyGrp",
]

CLEANING_LOG: list[str] = []

_BASE_IRR = {"One": 1, "Two": 2, "Three": 3, "Four": 4}


def _log(msg: str) -> None:
    if msg not in CLEANING_LOG:
        CLEANING_LOG.append(msg)


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(RAW_CSV, encoding="latin1")
    df.columns = df.columns.str.strip()
    return df


def load_clean() -> pd.DataFrame:
    """Return the analysis-ready table: one row per plot."""
    df = load_raw()

    # Anonymised placeholders carry no information.
    df = df.drop(columns=["FarmerName", "MobileNumber"])
    _log("Dropped FarmerName and MobileNumber (anonymised placeholders).")

    for col in ["Village", "Block", "District", "LandType", "SoilType",
                "PreviousCrop", "Variety", "ManualWeeding", "CropEstablishment"]:
        df[col] = df[col].astype("string").str.strip()

    df["SoilType"] = df["SoilType"].str.capitalize()
    _log("Harmonised SoilType case ('medium' -> 'Medium', 'light' -> 'Light').")

    df["PreviousCrop"] = (
        df["PreviousCrop"].str.capitalize().replace({"Paddy": "Rice"})
    )
    _log("Harmonised PreviousCrop ('Paddy'/'paddy'/'rice' -> 'Rice', case fixed).")

    top_varieties = ["HD2967", "HD2733", "DBW187", "HD2985"]
    df["VarietyGrp"] = df["Variety"].where(df["Variety"].isin(top_varieties), "Other")
    _log("Grouped varieties with <10 plots into 'Other'.")

    # Treatment indicator and farmer's own (base) irrigation count.
    df["Treated"] = (df["Plot"].str.strip() == "Treatment").astype(int)
    df["BaseIrrigations"] = df["IrrigationNumber"].str.strip().map(_BASE_IRR)
    df["IrrigationEvents"] = df[IRRIGATION_DAY_COLS].notna().sum(axis=1)

    # Consistency check: treated plots should have exactly base + 1 events.
    expected = df["BaseIrrigations"] + df["Treated"]
    df["FlagIrrigationMismatch"] = (df["IrrigationEvents"] != expected).astype(int)
    if df["FlagIrrigationMismatch"].any():
        _log(f"{int(df['FlagIrrigationMismatch'].sum())} plots have irrigation "
             "events inconsistent with treatment arm.")
    else:
        _log("Irrigation events match arm for every plot "
             "(control = base, treatment = base + 1).")

    df["FlagControlWithAddlDate"] = (
        (df["Treated"] == 0) & df["DateofAdditionalIrrigation"].notna()
    ).astype(int)
    n = int(df["FlagControlWithAddlDate"].sum())
    if n:
        _log(f"{n} control plots carry a DateofAdditionalIrrigation but no extra "
             "irrigation event; kept as controls and flagged (likely data-entry).")

    # Fertiliser: missing means 'not applied' for optional products.
    df["UsedDAP"] = df["BasalDAP"].notna().astype(int)
    df["UsedNPK"] = df["BasalNPK"].notna().astype(int)
    df["UsedZn"] = df["BasalZn"].notna().astype(int)
    df["BasalDAP_f"] = df["BasalDAP"].fillna(0.0)
    df["Split3Urea_f"] = df["Split3Urea"].fillna(0.0)
    _log("Missing BasalDAP/BasalNPK/BasalZn/Split3Urea treated as 'not applied' "
         "(0 + usage flag).")

    df["ManualWeedingYes"] = (df["ManualWeeding"].str.lower() == "yes").astype(int)
    df["ZeroTillage"] = (df["CropEstablishment"] == "ZT").astype(int)

    # Locality clusters used for robust standard errors.
    df["ClusterBlockYear"] = df["Block"] + "|" + df["Year"]
    df["DistrictYear"] = df["District"] + "|" + df["Year"]
    df["MatchSet"] = (
        df["Year"] + "|" + df["Block"] + "|" + df["Village"] + "|"
        + df["SowingDate"].astype("string") + "|" + df["Variety"] + "|"
        + df["CropEstablishment"]
    )
    return df.reset_index(drop=True)


def design_matrix(df: pd.DataFrame, drop_first: bool = True) -> pd.DataFrame:
    """Numeric covariate matrix X (pre-treatment only) for modelling."""
    X = df[NUMERIC_COVARIATES + FLAG_COVARIATES].astype(float)
    dummies = pd.get_dummies(
        df[CATEGORICAL_COVARIATES].astype(str), drop_first=drop_first, dtype=float
    )
    X = pd.concat([X, dummies], axis=1)
    X.columns = [str(c).replace(" ", "_") for c in X.columns]
    assert not X.isna().any().any(), "design matrix has missing values"
    return X


def smd(x: np.ndarray, t: np.ndarray, w: np.ndarray | None = None) -> float:
    """Standardised mean difference (weighted if w given). |SMD| > 0.1 = imbalance."""
    if w is None:
        w = np.ones_like(x, dtype=float)
    m1 = np.average(x[t == 1], weights=w[t == 1])
    m0 = np.average(x[t == 0], weights=w[t == 0])
    v1 = np.var(x[t == 1])
    v0 = np.var(x[t == 0])
    denom = np.sqrt((v1 + v0) / 2)
    return 0.0 if denom == 0 else (m1 - m0) / denom
