"""Semi-synthetic simulation: real farms, real covariates, KNOWN true effect.

Why semi-synthetic? In the real data we never know the true irrigation effect, so
we cannot tell which estimator is right. Here we keep every real plot's
covariates (district, season, sowing date, practices...) and the real locality
structure, but we generate the yield ourselves:

    Y = mu0(X) + tau(X) * T + cluster_shock(block x season) + plot_noise [+ gamma * U]

* mu0(X): a realistic baseline yield surface learnt from the real CONTROL plots.
* tau(X): the true effect of the extra irrigation, chosen by us (so it is known).
* T: treatment, assigned by a mechanism we control (randomised, real, or
  confounded with a tunable "imbalance dial" k).
* U: optional hidden confounder (e.g. better-managed farms), not given to methods.

Each estimator is then scored on bias, RMSE, 95% CI coverage and CI width.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from . import estimators as est

SIGMA_CLUSTER = 0.20   # shared block x season shock (t/ha), calibrated from residuals
SIGMA_PLOT = 0.45      # plot-level noise (t/ha), calibrated from residuals
TARGET_SHARE = 0.42    # real treated share


class World:
    """Fixed ingredients shared by every repetition (built once from real data)."""

    def __init__(self, df: pd.DataFrame, X: pd.DataFrame):
        self.df = df.reset_index(drop=True)
        self.X = X.reset_index(drop=True)
        ctrl = self.df.Treated == 0
        base = HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05,
                                             max_iter=300, random_state=0)
        base.fit(self.X[ctrl], self.df.GrainYield[ctrl])
        self.mu0 = base.predict(self.X)

        # Linear index of the REAL assignment, used for the imbalance dial.
        lr = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=3000))
        lr.fit(self.X, self.df.Treated)
        lin = lr.decision_function(self.X)
        self.real_index = (lin - lin.mean()) / lin.std()
        self.clusters = pd.factorize(self.df.ClusterBlockYear)[0]

        b = self.df.BaseIrrigations.to_numpy(float)
        late = (self.df.SowingWindow == "Late Sown").to_numpy(float)
        zt = self.df.ZeroTillage.to_numpy(float)
        self.tau_const = np.full(len(df), 0.80)
        # Heterogeneous truth: bigger benefit for farms that irrigated less and
        # for late-sown wheat (more terminal heat); agronomically plausible.
        self.tau_het = 0.80 + 0.25 * (2.6 - b) + 0.30 * (late - late.mean()) \
            + 0.10 * (zt - zt.mean())


def _sigmoid(z):
    return 1 / (1 + np.exp(-z))


def _calibrated_probs(index: np.ndarray, k: float) -> np.ndarray:
    """Propensity = sigmoid(a + k*index), with a chosen so mean = TARGET_SHARE."""
    lo, hi = -10.0, 10.0
    for _ in range(60):
        a = (lo + hi) / 2
        if _sigmoid(a + k * index).mean() < TARGET_SHARE:
            lo = a
        else:
            hi = a
    return _sigmoid(a + k * index)


def simulate(world: World, scenario: dict, rng: np.random.Generator) -> pd.DataFrame:
    """One simulated dataset (copy of real covariates with synthetic T and Y)."""
    n = len(world.df)
    tau = world.tau_het if scenario["effect"] == "heterogeneous" else world.tau_const

    hidden = np.zeros(n)
    if scenario["assign"] == "real":
        t = world.df.Treated.to_numpy()
    elif scenario["assign"] == "real+hidden":
        t = world.df.Treated.to_numpy()
        # Hidden 'farm management quality' U: higher among treated plots.
        u = rng.normal(0, 1, n) + scenario["hidden_shift"] * (t - t.mean())
        hidden = scenario["hidden_gamma"] * u
    elif scenario["assign"] == "dial":
        p = _calibrated_probs(world.real_index, scenario["k"])
        t = rng.binomial(1, p)
    else:
        raise ValueError(scenario["assign"])

    shock = rng.normal(0, SIGMA_CLUSTER, world.clusters.max() + 1)[world.clusters]
    y = world.mu0 + tau * t + shock + rng.normal(0, SIGMA_PLOT, n) + hidden

    sim = world.df.copy()
    sim["Treated"] = t
    sim["GrainYield"] = y
    sim.attrs["true_ate"] = float(tau.mean())
    sim.attrs["true_att"] = float(tau[t == 1].mean())
    return sim


def run_once(world: World, scenario: dict, rep: int, fast: bool = True) -> list[dict]:
    rng = np.random.default_rng(10_000 * scenario["id"] + rep)
    sim = simulate(world, scenario, rng)
    X = world.X
    out = []
    fns = [
        lambda: est.naive_difference(sim),
        lambda: est.ols_adjusted(sim, X),
        lambda: est.ols_district_year_fe(sim, X),
        lambda: est.matched_set_fe(sim, X),
    ]
    for f in fns:
        out.append(f())
    nu = est.cross_fit_nuisance(sim, X, seed=rep, fast=fast)
    for f in (est.ipw, est.aipw, est.dml_plr):
        out.append(f(sim, nu))
    for r in out:
        r.update(scenario=scenario["name"], scenario_id=scenario["id"], rep=rep,
                 true_ate=sim.attrs["true_ate"], true_att=sim.attrs["true_att"],
                 treated_share=float(sim.Treated.mean()))
    return out


def scenarios() -> list[dict]:
    S = []
    i = 0
    for effect in ["constant", "heterogeneous"]:
        for k, label in [(0.0, "Randomised (k=0)"), (0.5, "Mild imbalance (k=0.5)"),
                         (1.0, "Real-like imbalance (k=1)"), (2.0, "Severe imbalance (k=2)")]:
            S.append({"id": i, "assign": "dial", "k": k, "effect": effect,
                      "name": f"{label} | {effect} effect"})
            i += 1
    S.append({"id": i, "assign": "real", "effect": "heterogeneous",
              "name": "Actual trial assignment | heterogeneous effect"})
    i += 1
    S.append({"id": i, "assign": "real+hidden", "effect": "heterogeneous",
              "hidden_shift": 1.0, "hidden_gamma": 0.20,
              "name": "Actual assignment + hidden confounder | heterogeneous effect"})
    return S
