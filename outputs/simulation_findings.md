# Simulation Stress Test - Key Findings (interpretation)

Source numbers: `outputs/simulation_summary.md` (10 scenarios x 100 repetitions x 7 methods,
semi-synthetic: real 1,810 plots and covariates, synthetic yield with a known true effect).
Figures: `fig09_sim_rmse_heatmap.png`, `fig10_sim_imbalance_dial.png`, `fig11_sim_real_assignment.png`.

## F1. Simple comparisons break as imbalance grows
- Raw difference: bias 0.00 t/ha when randomised, -0.15 at real-like imbalance (k=1), -0.22 at k=2.
- Its 95% interval contains the truth only 3% of the time at k=1 (target 95%).
- Implication: the farmer-trial "average vs average" comparison is not reliable for this data.

## F2. The matched-set comparison is biased DOWNWARD - this explains the real-data puzzle
- Matched sets (same village, sowing date, variety, tillage) do not adjust for differences
  *inside* a set. The biggest one is the farmer's own irrigation count, which drives both
  who received the extra irrigation and baseline yield.
- Bias: -0.13 t/ha at k=1, -0.23 at k=2; coverage 32% and 1%.
- Real data gave matched-set +0.71 vs about +1.0 for adjusted methods. The simulation shows
  that this gap is what we would expect from this bias, so +0.71 should NOT be read as the
  "more honest" number.

## F3. Covariate-adjusting methods recover the truth when all confounders are measured
- Regression, district x season FE, IPW, AIPW and Double ML: |bias| <= 0.017 t/ha and
  coverage 0.90-1.00 for every imbalance level.
- Under the ACTUAL trial assignment (heterogeneous effect), Double ML was best:
  bias +0.023, RMSE 0.046, coverage 0.93. IPW/AIPW were unbiased-ish but noisy
  (RMSE ~0.09) because 14 district-seasons have no comparison group (poor overlap).
- Double ML intervals are slightly too narrow (coverage 0.84-0.93); IPW is conservative.

## F4. No method can fix a hidden confounder
- With an unmeasured factor (e.g. better-managed farms taking the extra irrigation) worth
  about +0.2 t/ha, every adjusted method overestimates by 0.23-0.28 t/ha with ~0% coverage.
- The matched-set estimate looked closer only because its downward bias (F2) happened to
  cancel the upward hidden bias - not a reason to trust it.
- Implication: the real-data estimate of about +1.0 t/ha is reliable only if there is no
  large hidden confounding. A sensitivity analysis (how strong would a hidden factor need to
  be to change the decision?) must accompany the result.

## Decisions for the next stage
1. Use the Double ML / causal-forest family (orthogonalised, cross-fitted) for the
   who-benefits model - best accuracy under the real assignment pattern.
2. Report overlap: flag recommendations for farm profiles that fall in no-comparison cells.
3. Add a sensitivity analysis for hidden confounding to every headline number.
4. Fix the matched-set method by adding within-set covariate adjustment (or drop it).

## Limits of this simulation
- The baseline yield surface and effect pattern are our assumptions (learnt from controls and
  chosen to be agronomically plausible); results show how methods behave in a world LIKE
  this one, not proof about the real effect.
- 100 repetitions per scenario: coverage values are accurate to about +/- 0.04.
