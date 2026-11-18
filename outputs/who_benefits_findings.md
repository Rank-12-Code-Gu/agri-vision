# Who Benefits? - Key Findings (interpretation)

Source numbers: `outputs/who_benefits_summary.md`. Figures 12-17. Model: `models/cate_forest.joblib`.
Method chosen because the simulation (`simulation_findings.md`) showed the Double ML family
is the most accurate under the real trial assignment. A causal forest is the
heterogeneous-effect version of Double ML.

## H1. The benefit really differs between farms (validated out-of-fold)
- Calibration slope 0.82 (p = 0.001): predictions of who benefits more carry real signal.
- Farms in the top fifth of predicted benefit gained +1.26 t/ha against +0.70 in the bottom
  fifth (difference +0.56 t/ha, p = 0.014). Each farm's prediction came from a forest that
  never saw its locality.
- Average effect (forest): +0.89 t/ha (95% CI 0.79-0.99), consistent with the baselines.

## H2. WHERE matters far more than farm practice
- District accounts for 87% of the forest's importance. Irrigations already given account
  for 9% and sowing date for 3%; tillage, soil and variety are negligible.
- Measured gains by district range from about +0.5 t/ha (Begusarai, East Champaran) to
  +1.4 to +1.9 (Bhojpur, Deoria).
- A district bundles weather (terminal heat), groundwater, soils and the KVK team running
  the trial. This model cannot separate them yet. **Next step:** add district-season
  temperature during grain filling (NASA POWER) and test whether heat explains the district
  pattern. If it does, the advice becomes weather-driven and works for new seasons.
- Lakhisarai's interval is very wide (-1.4 to +1.1). Treat it as "no reliable estimate".

## H3. Farm practice: diminishing returns at 4 irrigations
- Farms that had already given 4 irrigations gained least: +0.45 t/ha (CI 0.12-0.77),
  against +0.72 to +1.14 for 1-3 irrigations. This fits agronomic intuition (a well-watered
  crop gains less), but n = 145 with only 29 treated.
- Sowing window, tillage, soil and land type: no clear differences (overlapping CIs).
  Late-sown plots are few (243), so the expected larger heat benefit cannot be confirmed.

## H4. Economics: at current prices the extra irrigation pays almost everywhere
- Break-even gain = Rs 2,500/ha cost / (Rs 2,425/quintal x 10) = 0.10 t/ha. These are
  assumptions in `src/agrivision/economics.py` and need verifying.
- Every plot's predicted gain, including its 95% lower bound, is above break-even.
  Median net benefit is about Rs 19,700/ha.
- So the honest message is "the extra irrigation is worth it" rather than "most farmers
  should skip it". Targeting adds value when **water or diesel is limited**:
  - With water for 25% of farms, priority order gives 0.293 t/ha average gain vs 0.241
    random (+22%). At 50% it is 0.570 vs 0.482 (+18%).
  - This targeting gain is modest. Report it as such.

## Caveats (carry into every slide)
1. Hidden confounding (simulation F4) applies here too: all effects assume no large
   unmeasured factor drove who got the extra irrigation.
2. District effects may partly reflect how each KVK ran and measured the trial.
3. Economic numbers depend on price and cost assumptions.

## Next steps
- Weather layer: grain-filling heat per district-season -> does heat explain the district
  differences? This is the key scientific test and makes the product weather-aware.
- Sensitivity analysis for hidden confounding on the headline numbers.
- Dashboard built on `models/cate_forest.joblib`.
