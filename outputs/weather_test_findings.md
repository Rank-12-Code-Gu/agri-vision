# Weather Test - Key Findings (interpretation)

Source numbers: `outputs/weather_test_summary.md`. Figures 18-20. Weather: NASA POWER daily
(MERRA-2), 25 grid cells, grain-filling window 95-125 days after each plot's sowing date.

## W1. Grain-filling heat does NOT explain who benefits (a clear negative result)
- Heat days (Tmax > 34 C) vary a lot: from 1 day (2019-20) to 22 days (2017-18) per season.
  That is plenty of contrast to detect an effect.
- Effect change per +9 heat days (1 SD): +0.015 t/ha (95% CI -0.15 to +0.18, p = 0.86).
  Within the same district across seasons: +0.001 (p = 0.98).
- The result holds for every window tested (85-115, 95-125, 105-135 days) and every
  threshold (32, 34, 36 C). No combination comes close to significance.
- Rain during grain filling does not reduce the benefit either (p = 0.21).

## W2. The benefit is even large in cool, rainy seasons
- 2019-20 had about 1 heat day and about 65 mm of rain in grain filling. Gains still reached
  +2.6 t/ha (Deoria), +2.0 (Kushinagar) and +1.4 (Bhojpur, Muzaffarpur).
- The trial was designed to test "irrigation at grain filling protects against terminal
  heat". This data cannot support heat protection as the mechanism.
- Two explanations remain open:
  - (a) a different mechanism, e.g. general soil-moisture deficit late in the season;
  - (b) treated plots differed in more than one irrigation (better attention or management
    on demonstration plots), i.e. hidden confounding.
  Explanation (b) would also explain why a single irrigation appears to add about 25% yield.
  This makes the planned sensitivity analysis essential.

## W3. District differences are real and persistent, and weather does not explain them
- Weather varies by season (75% of heat-day variation) and hardly by district (3.5%).
  It therefore cannot explain district differences.
- After adding heat and rain, the spread of district effects is unchanged (0.539 -> 0.536
  t/ha). District stays highly significant (p < 1e-40); weather adds nothing (p = 0.58).
- Cross-check with a simple within-season regression per district gives the same ranking:
  - Low (about +0.5-0.6 t/ha): Begusarai, East Champaran, Lakhisarai, Rohtas
  - High (about +1.6-1.9 t/ha): Kushinagar, Deoria
  - Madhepura cannot be estimated reliably (only 2 seasons, unstable fit).

## W4. Prediction test: district knowledge transfers to a NEW season; weather does not
- District + practice model, predicting a held-out season: calibration slope 0.80 (p = 0.001).
  The district ranking holds year after year.
- Weather + practice model: works for a new locality within known seasons (0.89) but fails
  for a new season (-0.09). Weather only acted as a "season fingerprint"; it did not capture
  a real mechanism.
- Practice-only model: no skill in either test.

## W5. Method note: doubly robust scores can break in small cells
- Lakhisarai 2018-19 showed -2.21 t/ha in Figure 18, but its raw within-cell difference is
  +0.45 (18 vs 20 plots). The doubly robust score is unstable where the models extrapolate.
- The per-district regression cross-check gives Lakhisarai +0.59, so -2.21 is an artifact.
  Per-cell numbers should always be cross-checked with a simpler estimator.

## What this means for the product
- Drop the "weather-aware" claim. The evidence does not support adjusting advice by heat
  forecast, and presenting it would be indefensible.
- What is supported: the district (location) is the strongest and most stable predictor
  of how much farms gain. Advice should be **district-specific**, with farm practice
  (irrigations already given) as a secondary factor.
- The headline research finding for the panel: "The extra irrigation was designed to
  protect against terminal heat, but its benefit does not depend on heat at all. It
  depends on location, consistently across six seasons." This is novel, defensible, and
  backed by multiple tests.

## Next steps
1. Sensitivity analysis: how strong would a hidden factor need to be to explain away the
   gain, or the district differences?
2. Investigate what makes Deoria and Kushinagar (both Uttar Pradesh) different from
   Begusarai and East Champaran: soil, groundwater depth, KVK protocol. The state
   difference is worth testing.
3. Dashboard: district-specific advice + practice + honest uncertainty, no weather claim.
