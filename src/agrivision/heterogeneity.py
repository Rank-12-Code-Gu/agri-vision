"""Who benefits? Heterogeneous effect (CATE) model with a causal forest.

Effect modifiers (X_mod) are things known at decision time and easy to enter in the
dashboard. Everything else is a control (W) used only to remove confounding.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from econml.dml import CausalForestDML
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold

MODIFIER_NUMERIC = ["SowingDay", "BaseIrrigations", "ZeroTillage"]
MODIFIER_CATEGORICAL = ["District", "SoilType", "LandType", "VarietyGrp"]

CONTROL_NUMERIC = [
    "SeedRate", "PrevCropResidue", "FirstIrrigationDay", "BasalDAP_f", "BasalMOP",
    "Split1Urea", "Split2Urea", "Split3Urea_f", "Latitude", "Longitude",
    "UsedDAP", "UsedNPK", "UsedZn", "ManualWeedingYes",
]
CONTROL_CATEGORICAL = ["Year", "PreviousCrop"]


def modifier_levels(df: pd.DataFrame, categorical=None) -> dict[str, list[str]]:
    categorical = MODIFIER_CATEGORICAL if categorical is None else categorical
    return {c: sorted(df[c].astype(str).unique()) for c in categorical}


def build_modifiers(df: pd.DataFrame, levels: dict[str, list[str]],
                    numeric=None) -> pd.DataFrame:
    """One-hot with FIXED levels so the dashboard builds identical columns.

    `levels` decides which categorical modifiers are used; `numeric` overrides the
    default numeric modifier list.
    """
    numeric = MODIFIER_NUMERIC if numeric is None else numeric
    X = df[numeric].astype(float).copy()
    for c in levels:
        vals = df[c].astype(str)
        for lev in levels[c]:
            X[f"{c}={lev}"] = (vals == lev).astype(float)
    return X


def build_controls(df: pd.DataFrame) -> pd.DataFrame:
    W = df[CONTROL_NUMERIC].astype(float)
    d = pd.get_dummies(df[CONTROL_CATEGORICAL].astype(str), drop_first=True, dtype=float)
    return pd.concat([W, d], axis=1)


def new_forest(seed: int = 0) -> CausalForestDML:
    kw = dict(max_depth=3, learning_rate=0.05, max_iter=300, random_state=seed)
    return CausalForestDML(
        model_y=HistGradientBoostingRegressor(**kw),
        model_t=HistGradientBoostingClassifier(**kw),
        discrete_treatment=True,
        cv=GroupKFold(n_splits=5),
        n_estimators=2000,
        min_samples_leaf=20,
        max_samples=0.45,
        honest=True,
        inference=True,
        random_state=seed,
    )


def fit_forest(df, Xm, W, seed=0) -> CausalForestDML:
    cf = new_forest(seed)
    cf.fit(df.GrainYield.to_numpy(float), df.Treated.to_numpy(), X=Xm.to_numpy(),
           W=W.to_numpy(), groups=pd.factorize(df.ClusterBlockYear)[0])
    return cf


def out_of_fold_cate(df, Xm, W, n_splits=5, seed=0, split_by="ClusterBlockYear") -> np.ndarray:
    """CATE for each plot predicted by a forest that never saw its group.

    split_by="ClusterBlockYear": never saw the plot's locality-season.
    split_by="Year" (n_splits=6): leave-one-season-out, i.e. a brand-new season.
    """
    groups = pd.factorize(df[split_by])[0]
    perm = np.random.default_rng(seed).permutation(groups.max() + 1)
    oof = np.zeros(len(df))
    for tr, te in GroupKFold(n_splits=n_splits).split(Xm, groups=perm[groups]):
        cf = fit_forest(df.iloc[tr].reset_index(drop=True), Xm.iloc[tr], W.iloc[tr], seed)
        oof[te] = cf.effect(Xm.iloc[te].to_numpy())
    return oof


def dr_scores(df, nu, trim=(0.05, 0.95)) -> np.ndarray:
    """Doubly robust pseudo-outcome per plot: its mean over any group = AIPW effect."""
    y, t = df.GrainYield.to_numpy(float), df.Treated.to_numpy()
    e = np.clip(nu["e"], *trim)
    return nu["m1"] - nu["m0"] + t * (y - nu["m1"]) / e - (1 - t) * (y - nu["m0"]) / (1 - e)


def cluster_mean(psi: np.ndarray, groups) -> tuple[float, float]:
    n = len(psi)
    m = psi.mean()
    s = pd.Series(psi - m).groupby(pd.factorize(groups)[0]).sum().to_numpy()
    return float(m), float(np.sqrt((s ** 2).sum()) / n)
