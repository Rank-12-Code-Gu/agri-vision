"""Baseline estimators of the average effect of the extra irrigation (ATE).

Each function returns a dict: estimate, se, ci_low, ci_high, n, method, note.
Standard errors are cluster-robust (block x season) wherever possible, because
plots in the same locality and season share weather and management.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

Z = 1.959963984540054


def _result(method, est, se, n, note=""):
    return {"method": method, "estimate": float(est), "se": float(se),
            "ci_low": float(est - Z * se), "ci_high": float(est + Z * se),
            "n": int(n), "note": note}


def _ols(y, X, groups, method, note=""):
    X = sm.add_constant(X, has_constant="add")
    fit = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(groups)[0]})
    return _result(method, fit.params["Treated"], fit.bse["Treated"], len(y), note)


def naive_difference(df):
    y, t = df.GrainYield.to_numpy(), df.Treated.to_numpy()
    est = y[t == 1].mean() - y[t == 0].mean()
    se = np.sqrt(y[t == 1].var(ddof=1) / (t == 1).sum() + y[t == 0].var(ddof=1) / (t == 0).sum())
    return _result("1. Raw difference", est, se, len(y), "no adjustment, i.i.d. SE")


def ols_adjusted(df, X):
    Xd = pd.concat([df[["Treated"]].astype(float), X], axis=1)
    return _ols(df.GrainYield, Xd, df.ClusterBlockYear,
                "2. Regression + covariates", "season & district dummies + practices")


def ols_district_year_fe(df, X):
    drop = [c for c in X.columns if c.startswith(("Year_", "District_"))]
    fe = pd.get_dummies(df.DistrictYear, drop_first=True, dtype=float, prefix="DY")
    Xd = pd.concat([df[["Treated"]].astype(float), X.drop(columns=drop), fe], axis=1)
    return _ols(df.GrainYield, Xd, df.ClusterBlockYear,
                "3. Regression + district x season FE",
                "compares plots within the same district and season")


def matched_set_fe(df, X):
    """Within-match-set comparison: only sets containing both arms."""
    s = df.groupby("MatchSet").Treated.transform(lambda v: 0 < v.mean() < 1)
    sub = df[s].copy()
    # Demean outcome and treatment within each set (equivalent to set fixed effects).
    yd = sub.GrainYield - sub.groupby("MatchSet").GrainYield.transform("mean")
    td = sub.Treated - sub.groupby("MatchSet").Treated.transform("mean")
    fit = sm.OLS(yd.to_numpy(), td.to_numpy()[:, None]).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(sub.MatchSet)[0]})
    return _result("4. Matched-set comparison", fit.params[0], fit.bse[0], len(sub),
                   f"{sub.MatchSet.nunique()} sets with both arms only")


# ------------------------------------------------------------------ propensity based
def cross_fit_nuisance(df, X, n_splits=5, seed=0, learner="gbm", fast=False):
    """Out-of-fold propensity e(x) and outcome models m0(x), m1(x), m(x).

    Folds are grouped by block x season so a locality never appears in both the
    training and prediction fold (avoids optimistic leakage).
    """
    y, t = df.GrainYield.to_numpy(float), df.Treated.to_numpy()
    Xv = X.to_numpy(float)
    groups = pd.factorize(df.ClusterBlockYear)[0]
    e = np.zeros(len(y)); m0 = np.zeros(len(y)); m1 = np.zeros(len(y)); m = np.zeros(len(y))
    rng = np.random.default_rng(seed)
    perm = rng.permutation(groups.max() + 1)
    # fast=True (used in simulations): fewer, larger boosting steps.
    kw = dict(max_depth=3, learning_rate=0.1 if fast else 0.05,
              max_iter=150 if fast else 300, random_state=seed)
    for tr, te in GroupKFold(n_splits=n_splits).split(Xv, y, perm[groups]):
        if learner == "logit":
            ps = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000))
        else:
            ps = HistGradientBoostingClassifier(**kw)
        ps.fit(Xv[tr], t[tr])
        e[te] = ps.predict_proba(Xv[te])[:, 1]
        for arm, store in [(0, m0), (1, m1)]:
            idx = tr[t[tr] == arm]
            store[te] = HistGradientBoostingRegressor(**kw).fit(Xv[idx], y[idx]).predict(Xv[te])
        m[te] = HistGradientBoostingRegressor(**kw).fit(Xv[tr], y[tr]).predict(Xv[te])
    return {"e": e, "m0": m0, "m1": m1, "m": m}


def _cluster_se_from_if(psi, groups):
    """SE of a mean of influence-function values, clustered by group."""
    n = len(psi)
    centred = psi - psi.mean()
    s = pd.Series(centred).groupby(pd.factorize(groups)[0]).sum().to_numpy()
    return np.sqrt((s ** 2).sum()) / n


def ipw(df, nu, trim=(0.05, 0.95)):
    y, t = df.GrainYield.to_numpy(float), df.Treated.to_numpy()
    e = np.clip(nu["e"], *trim)
    w1, w0 = t / e, (1 - t) / (1 - e)
    mu1 = (w1 * y).sum() / w1.sum()
    mu0 = (w0 * y).sum() / w0.sum()
    psi = w1 * (y - mu1) / w1.mean() - w0 * (y - mu0) / w0.mean()
    se = _cluster_se_from_if(psi + (mu1 - mu0), df.ClusterBlockYear)
    return _result("5. Inverse propensity weighting", mu1 - mu0, se, len(y),
                   f"stabilised weights, propensity clipped to {trim}")


def aipw(df, nu, trim=(0.05, 0.95)):
    y, t = df.GrainYield.to_numpy(float), df.Treated.to_numpy()
    e = np.clip(nu["e"], *trim)
    psi = (nu["m1"] - nu["m0"]
           + t * (y - nu["m1"]) / e
           - (1 - t) * (y - nu["m0"]) / (1 - e))
    return _result("6. Doubly robust (AIPW)", psi.mean(),
                   _cluster_se_from_if(psi, df.ClusterBlockYear), len(y),
                   "ML outcome + propensity models, cross-fitted")


def dml_plr(df, nu):
    """Double ML, partially linear model: residual-on-residual regression."""
    y, t = df.GrainYield.to_numpy(float), df.Treated.to_numpy(float)
    ry, rt = y - nu["m"], t - nu["e"]
    theta = (rt * ry).sum() / (rt ** 2).sum()
    psi = rt * (ry - theta * rt) / (rt ** 2).mean()
    return _result("7. Double ML (partially linear)", theta,
                   _cluster_se_from_if(psi + theta, df.ClusterBlockYear), len(y),
                   "cross-fitted gradient boosting")
