# Sensitivity to Hidden Confounding - Key Findings (interpretation)

Source numbers: `outputs/sensitivity_summary.md`. Figures 21-23. Script: `scripts/07_sensitivity.py`.

## S1. The negative-control test FAILS: there is real hidden confounding
- The extra irrigation was given at a median of 108 days after sowing (IQR 104-113; 96% at
  >= 100 days). By then the number of ears (effective tillers) is already fixed. A late
  irrigation cannot create ears.
- After the same adjustment used for yield, treated plots still have **+13 to +15% more ears**
  (95% CI about 10-19%). Both the regression and Double ML agree. Restricting to irrigation
  >= 100 days changes nothing.
- This "effect" is impossible, so it measures hidden differences between plots: better crop
  stands, management, or plot choice on the demonstration plots. Measured covariates do not
  capture them.
- Grains per ear (+6 to +8%) is also mostly fixed before the irrigation. 1000-grain weight,
  the channel a grain-filling irrigation can actually change, is only **+2.3 to +2.5%**.

## S2. Corrected size of the effect: probably 0.2-0.5 t/ha, not ~1.1
Yield = ears x grains per ear x grain weight, so removing the impossible channels gives a
calibrated range:

| Version | % gain | t/ha (at control mean 3.89) |
|---|---|---|
| Uncorrected (adjusted) | +28 to +30% | about 1.1 (0.9-1.4) |
| Ear-count channel removed | +12 to +13% | about 0.5 (0.34-0.66) |
| Ear + grain-number channels removed | +5 to +6% | about 0.2 (0.07-0.38) |

- The lower value assumes the hidden factor works only through ears and grains. If it also
  raises grain weight, the true effect is lower still. If the irrigation helps grain set a
  little, the true effect sits nearer the middle value. **Defensible range: about 0.2-0.5 t/ha.**
- Economics still hold: break-even is 0.10 t/ha (assumed prices), so even the conservative
  0.2 t/ha (about Rs 4,850/ha value vs Rs 2,500 cost) pays. The size of the benefit is
  roughly half to a fifth of the naive estimate.

## S3. Formal sensitivity statistics alone would have given false comfort
- Robustness value RV = 0.52 means a hidden factor would need to explain 52% of the remaining
  variation in both treatment and yield to erase the effect. A hidden factor as strong as the
  district x season cells would cut it to 0.68 t/ha. That sounds robust.
- But the negative control shows confounding big enough to remove about half the effect
  (RV needed for that: 0.32). Formal bounds describe *how big* a confounder must be. Only the
  agronomic negative control showed that one this big exists.
- **Methodological lesson (a contribution of this project):** for on-farm trials,
  yield-component negative controls are a cheap, data-already-collected check that standard
  causal-ML pipelines skip.

## S4. The district differences are largely confounding as well
- Across districts, the yield "effect" and the impossible ear "effect" are correlated at
  **0.76**. Muzaffarpur's +39% yield gain is matched by a +38% ear gain, i.e. essentially
  all confounding.
- After removing the ear channel (yield per ear), a smaller pattern remains: Deoria +28%,
  Kushinagar +17%, Buxar +16% vs Begusarai +6%, Rohtas +5%, Lakhisarai +2%, Muzaffarpur +1%.
  Some location difference may be real, but it is far smaller than the raw district ranking.
- So the weather-test conclusion "district drives the benefit" must be downgraded to:
  "district mainly drives *how differently the trial plots were chosen or managed*".

## What this means for the project
1. **The research story now has a strong, original core:**
   - (i) naive estimates disagree (baselines);
   - (ii) causal ML is the most accurate when all confounders are measured (simulation);
   - (iii) but a yield-component negative control shows they were not all measured;
   - (iv) the corrected effect is 0.2-0.5 t/ha, still profitable.
   Few student, or even published, on-farm analyses go this far.
2. **Product change:** the decision engine should report the corrected range, not 1.1 t/ha.
   District-specific advice should use the ear-corrected (yield-per-ear) effects, with wide
   uncertainty, and clearly say "trial plots may differ from typical fields".
3. **Policy/advice:** the extra irrigation still pays at assumed prices, but the trial data
   overstate the gain by roughly 2-5x. Future trials should pair treatment and control on
   the same field (truly randomised strips) to avoid this.

## Caveats
- Ear counts and grain counts are field measurements with their own error. A systematic
  counting difference between arms would also produce S1.
- The calibration assumes yield is multiplicative in its components. Measured yield and the
  component product correlate at 0.67 on the log scale, so the decomposition is approximate.
- Price and cost figures remain assumptions (`src/agrivision/economics.py`).
