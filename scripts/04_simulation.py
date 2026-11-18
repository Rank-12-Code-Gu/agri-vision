"""Simulation stress test of the 7 estimators (known true effect).

Run from the project root:
    .venv/Scripts/python scripts/04_simulation.py --reps 100
Writes outputs/tables/simulation_*.csv, figures 09-11, outputs/simulation_summary.md.
Use --reps 2 for a quick smoke test.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")  # one thread per worker process

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from joblib import Parallel, delayed

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agrivision.data import design_matrix, load_clean  # noqa: E402
from agrivision.simulation import World, run_once, scenarios  # noqa: E402

FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"
FIG.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 10})



def summarise(raw: pd.DataFrame) -> pd.DataFrame:
    raw = raw.copy()
    raw["err"] = raw.estimate - raw.true_ate
    raw["covered"] = (raw.ci_low <= raw.true_ate) & (raw.true_ate <= raw.ci_high)
    raw["width"] = raw.ci_high - raw.ci_low
    g = raw.groupby(["scenario_id", "scenario", "method"])
    s = g.agg(true_ate=("true_ate", "mean"), mean_est=("estimate", "mean"),
              bias=("err", "mean"), rmse=("err", lambda e: np.sqrt((e ** 2).mean())),
              coverage=("covered", "mean"), ci_width=("width", "mean"),
              mean_reported_se=("se", "mean"), empirical_sd=("estimate", "std"),
              reps=("rep", "nunique")).reset_index()
    return s


def main():

    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=100)
    ap.add_argument("--jobs", type=int, default=-1)
    args = ap.parse_args()

    df = load_clean()
    X = design_matrix(df)
    world = World(df, X)
    S = scenarios()
    t0 = time.time()
    rows = Parallel(n_jobs=args.jobs, verbose=5)(
        delayed(run_once)(world, sc, r, True) for sc in S for r in range(args.reps))
    raw = pd.DataFrame([x for batch in rows for x in batch])
    raw.to_csv(TAB / "simulation_raw.csv", index=False)
    s = summarise(raw)
    s.to_csv(TAB / "simulation_summary.csv", index=False)
    print(f"done in {time.time() - t0:.0f}s, {len(raw)} estimates")
    report(s, raw, args.reps)


def report(s: pd.DataFrame, raw: pd.DataFrame, reps: int):
    methods = sorted(s.method.unique())
    short = {m: m.split(". ", 1)[1] for m in methods}

    # Figure 09: RMSE heatmap, scenario x method
    piv = s.pivot(index="scenario", columns="method", values="rmse")
    order = s.drop_duplicates("scenario").sort_values("scenario_id").scenario
    piv = piv.loc[order, methods]
    fig, ax = plt.subplots(figsize=(11, 5.6))
    im = ax.imshow(piv.values, cmap="YlOrRd", aspect="auto", vmin=0,
                   vmax=max(0.4, float(np.nanmax(piv.values))))
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.values[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8,
                    color="white" if v > 0.3 else "black")
    ax.set_xticks(range(len(methods)), [short[m] for m in methods], rotation=25, ha="right")
    ax.set_yticks(range(len(order)), order, fontsize=8)
    ax.set_title("Error of each method (RMSE, t/ha) when the true effect is known\n"
                 "lower = better")
    fig.colorbar(im, ax=ax, shrink=0.8, label="RMSE (t/ha)")
    fig.tight_layout()
    fig.savefig(FIG / "fig09_sim_rmse_heatmap.png")
    plt.close(fig)

    # Figure 10: imbalance dial (bias and coverage vs k), heterogeneous effect
    dial = s[s.scenario.str.contains(r"k=") & s.scenario.str.contains("heterogeneous")].copy()
    dial["k"] = dial.scenario.str.extract(r"k=([\d.]+)").astype(float)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for m in methods:
        d = dial[dial.method == m].sort_values("k")
        axes[0].plot(d.k, d.bias, marker="o", label=short[m])
        axes[1].plot(d.k, d.coverage, marker="o", label=short[m])
    axes[0].axhline(0, color="#333", lw=0.8)
    axes[0].set_xlabel("Imbalance dial k (0 = randomised, 1 = like real data)")
    axes[0].set_ylabel("Bias (t/ha)")
    axes[0].set_title("Bias as treatment assignment gets more unequal")
    axes[1].axhline(0.95, color="#333", lw=0.8, ls="--")
    axes[1].set_ylim(0, 1.02)
    axes[1].set_xlabel("Imbalance dial k")
    axes[1].set_ylabel("95% CI coverage (target 0.95)")
    axes[1].set_title("Is the reported uncertainty honest?")
    axes[1].legend(fontsize=7.5, frameon=False, loc="lower left")
    fig.tight_layout()
    fig.savefig(FIG / "fig10_sim_imbalance_dial.png")
    plt.close(fig)

    # Figure 11: estimate distributions under real assignment, with/without hidden confounder
    real = raw[raw.scenario.str.startswith("Actual")]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharex=True)
    for ax, (name, d) in zip(axes, real.groupby("scenario", sort=False)):
        data = [d[d.method == m].estimate.to_numpy() for m in methods]
        ax.boxplot(data, vert=False, tick_labels=[short[m] for m in methods], showfliers=False)
        ax.axvline(d.true_ate.mean(), color="#1b7f5a", lw=2, label="True ATE")
        ax.set_title(name.split(" | ")[0], fontsize=10)
        ax.set_xlabel("Estimated effect (t/ha)")
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle("Real trial assignment: which methods recover the truth?")
    fig.tight_layout()
    fig.savefig(FIG / "fig11_sim_real_assignment.png")
    plt.close(fig)

    # Markdown
    L = ["# Agri-Vision - Simulation Stress Test", "",
         f"Semi-synthetic design: 1,810 real plots and covariates, synthetic yields with a "
         f"KNOWN true effect. {reps} repetitions per scenario. Errors are measured against "
         "the true average treatment effect (ATE).", "",
         "Noise calibrated from real control-plot residuals: block x season shock "
         "sd 0.20 t/ha, plot noise sd 0.45 t/ha.", ""]
    for sid, d in s.groupby("scenario_id"):
        L += [f"## {d.scenario.iloc[0]}", f"True ATE = {d.true_ate.iloc[0]:.3f} t/ha", "",
              d[["method", "mean_est", "bias", "rmse", "coverage", "ci_width",
                 "mean_reported_se", "empirical_sd"]].round(3).to_markdown(index=False), ""]
    best = (s.groupby("method")[["rmse"]].mean().join(
        s.assign(cov_gap=(s.coverage - 0.95).abs()).groupby("method")[["cov_gap"]].mean())
        .sort_values("rmse"))
    L += ["## Overall ranking (mean over all scenarios)", "",
          best.round(3).to_markdown(), ""]
    (ROOT / "outputs" / "simulation_summary.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
