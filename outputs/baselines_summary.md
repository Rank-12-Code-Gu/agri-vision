# Agri-Vision - Baseline Effect Estimates

Outcome: grain yield (t/ha). Treatment: one extra irrigation at grain filling.
Standard errors clustered by block x season. Only pre-treatment covariates used.

## Estimates

| method                               |   estimate |    se |   ci_low |   ci_high |   % of control mean |    n | note                                                   |
|:-------------------------------------|-----------:|------:|---------:|----------:|--------------------:|-----:|:-------------------------------------------------------|
| 1. Raw difference                    |      0.916 | 0.04  |    0.837 |     0.996 |                23.6 | 1810 | no adjustment, i.i.d. SE                               |
| 2. Regression + covariates           |      1.12  | 0.073 |    0.977 |     1.262 |                28.8 | 1810 | season & district dummies + practices                  |
| 3. Regression + district x season FE |      1.093 | 0.08  |    0.937 |     1.25  |                28.1 | 1810 | compares plots within the same district and season     |
| 4. Matched-set comparison            |      0.714 | 0.083 |    0.551 |     0.877 |                18.4 |  504 | 189 sets with both arms only                           |
| 5. Inverse propensity weighting      |      1.001 | 0.07  |    0.864 |     1.137 |                25.8 | 1810 | stabilised weights, propensity clipped to (0.05, 0.95) |
| 6. Doubly robust (AIPW)              |      0.963 | 0.09  |    0.786 |     1.14  |                24.8 | 1810 | ML outcome + propensity models, cross-fitted           |
| 7. Double ML (partially linear)      |      1.021 | 0.078 |    0.867 |     1.174 |                26.3 | 1810 | cross-fitted gradient boosting                         |

Spread across methods: +0.714 to +1.120 t/ha (range 0.405).

## Propensity / overlap diagnostics

- Cross-fitted propensity AUC: **0.840** (0.5 = assignment unpredictable = like randomisation; near 1 = groups very different).
- Plots with propensity outside [0.05, 0.95]: 14.1%.
- District x season cells that are 0% or 100% treated (no comparison group inside the cell): **14 of 56**, holding 315 plots.
- Covariates with |SMD| > 0.10: 21 before weighting, 17 after weighting (of 42).

## Stability of ML estimators over 10 random seeds

| method                          |   mean |   std |   min |   max |
|:--------------------------------|-------:|------:|------:|------:|
| 5. Inverse propensity weighting |  1.016 | 0.021 | 0.977 | 1.046 |
| 6. Doubly robust (AIPW)         |  1.007 | 0.025 | 0.955 | 1.037 |
| 7. Double ML (partially linear) |  1.006 | 0.018 | 0.973 | 1.028 |

## Robustness checks (AIPW)

| check                                                                  |   estimate |    se |    n |
|:-----------------------------------------------------------------------|-----------:|------:|-----:|
| Drop 36 flagged Bhojpur 2021-22 controls                               |      0.99  | 0.076 | 1774 |
| AIPW with logistic propensity                                          |      1.078 | 0.069 | 1810 |
| AIPW, propensity clipped to [0.10, 0.90]                               |      1.01  | 0.067 | 1810 |
| AIPW leaving out season 2016-17                                        |      1.075 | 0.078 | 1652 |
| AIPW leaving out season 2017-18                                        |      1.016 | 0.072 | 1422 |
| AIPW leaving out season 2018-19                                        |      1.036 | 0.075 | 1376 |
| AIPW leaving out season 2019-20                                        |      1.028 | 0.071 | 1308 |
| AIPW leaving out season 2020-21                                        |      0.928 | 0.137 | 1654 |
| AIPW leaving out season 2021-22                                        |      1.011 | 0.08  | 1638 |
| AIPW only district-seasons with 40-60% treated                         |      1.017 | 0.109 |  944 |
| District x season FE only district-seasons with 40-60% treated         |      1.062 | 0.103 |  944 |
| AIPW drop district-seasons that are 0% or 100% treated                 |      1.038 | 0.076 | 1495 |
| District x season FE drop district-seasons that are 0% or 100% treated |      1.09  | 0.081 | 1495 |
