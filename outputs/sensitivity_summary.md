# Agri-Vision - Sensitivity to Hidden Confounding

Extra irrigation timing: median 108 days after sowing (IQR 104-113; 96% at >= 100 DAS).

## A. Negative-control outcomes (adjusted % differences)

| sample                           | outcome                                           | role                  | method                          |   pct_effect |   ci_low |   ci_high |    n |
|:---------------------------------|:--------------------------------------------------|:----------------------|:--------------------------------|-------------:|---------:|----------:|-----:|
| all plots                        | Grain yield                                       | target                | District x season FE regression |        30.28 |    25.1  |     35.68 | 1810 |
| all plots                        | Grain yield                                       | target                | Double ML                       |        28.44 |    23.53 |     33.54 | 1810 |
| all plots                        | Ears (effective tillers) per m - CANNOT be caused | negative control      | District x season FE regression |        15.03 |    11    |     19.2  | 1810 |
| all plots                        | Ears (effective tillers) per m - CANNOT be caused | negative control      | Double ML                       |        13.32 |     9.55 |     17.22 | 1810 |
| all plots                        | Grains per ear - mostly fixed before irrigation   | near-negative control | District x season FE regression |         7.56 |     6.18 |      8.96 | 1810 |
| all plots                        | Grains per ear - mostly fixed before irrigation   | near-negative control | Double ML                       |         6.31 |     4.07 |      8.59 | 1810 |
| all plots                        | 1000-grain weight - grain-filling channel         | plausible channel     | District x season FE regression |         2.49 |     2.29 |      2.7  | 1810 |
| all plots                        | 1000-grain weight - grain-filling channel         | plausible channel     | Double ML                       |         2.29 |     1.95 |      2.62 | 1810 |
| all plots                        | Total biomass                                     | mixed                 | District x season FE regression |        13.76 |     9.87 |     17.8  | 1810 |
| all plots                        | Total biomass                                     | mixed                 | Double ML                       |        10.06 |     6.96 |     13.25 | 1810 |
| all plots                        | Yield per ear (ear-count channel removed)         | calibrated target     | District x season FE regression |        13.25 |     9.73 |     16.89 | 1810 |
| all plots                        | Yield per ear (ear-count channel removed)         | calibrated target     | Double ML                       |        12.22 |     8.82 |     15.72 | 1810 |
| all plots                        | Yield per grain (ears and grains removed)         | calibrated target     | District x season FE regression |         5.3  |     1.92 |      8.78 | 1810 |
| all plots                        | Yield per grain (ears and grains removed)         | calibrated target     | Double ML                       |         5.67 |     1.72 |      9.77 | 1810 |
| extra irrigation >= 100 DAS only | Grain yield                                       | target                | District x season FE regression |        30.4  |    25.27 |     35.74 | 1781 |
| extra irrigation >= 100 DAS only | Grain yield                                       | target                | Double ML                       |        27.69 |    22.54 |     33.05 | 1781 |
| extra irrigation >= 100 DAS only | Ears (effective tillers) per m - CANNOT be caused | negative control      | District x season FE regression |        15.06 |    11.03 |     19.22 | 1781 |
| extra irrigation >= 100 DAS only | Ears (effective tillers) per m - CANNOT be caused | negative control      | Double ML                       |        13.77 |     9.91 |     17.78 | 1781 |
| extra irrigation >= 100 DAS only | Grains per ear - mostly fixed before irrigation   | near-negative control | District x season FE regression |         7.5  |     6.11 |      8.91 | 1781 |
| extra irrigation >= 100 DAS only | Grains per ear - mostly fixed before irrigation   | near-negative control | Double ML                       |         6.9  |     4.93 |      8.89 | 1781 |
| extra irrigation >= 100 DAS only | 1000-grain weight - grain-filling channel         | plausible channel     | District x season FE regression |         2.51 |     2.3  |      2.71 | 1781 |
| extra irrigation >= 100 DAS only | 1000-grain weight - grain-filling channel         | plausible channel     | Double ML                       |         2.4  |     2.11 |      2.69 | 1781 |
| extra irrigation >= 100 DAS only | Total biomass                                     | mixed                 | District x season FE regression |        13.66 |     9.78 |     17.68 | 1781 |
| extra irrigation >= 100 DAS only | Total biomass                                     | mixed                 | Double ML                       |         9.24 |     6.09 |     12.49 | 1781 |
| extra irrigation >= 100 DAS only | Yield per ear (ear-count channel removed)         | calibrated target     | District x season FE regression |        13.34 |     9.92 |     16.87 | 1781 |
| extra irrigation >= 100 DAS only | Yield per ear (ear-count channel removed)         | calibrated target     | Double ML                       |        11.31 |     7.97 |     14.75 | 1781 |
| extra irrigation >= 100 DAS only | Yield per grain (ears and grains removed)         | calibrated target     | District x season FE regression |         5.43 |     2.08 |      8.89 | 1781 |
| extra irrigation >= 100 DAS only | Yield per grain (ears and grains removed)         | calibrated target     | Double ML                       |         3.8  |     0.15 |      7.59 | 1781 |

### Calibrated effect (assumes the hidden factor acts through ear count / grain number)

| estimate                            | method                          |    pct |   t_per_ha_at_control_mean |   ci_low_t |   ci_high_t |
|:------------------------------------|:--------------------------------|-------:|---------------------------:|-----------:|------------:|
| Uncorrected                         | District x season FE regression | 30.279 |                      1.176 |      0.975 |       1.386 |
| Uncorrected                         | Double ML                       | 28.437 |                      1.105 |      0.914 |       1.303 |
| Ear-count channel removed           | District x season FE regression | 13.255 |                      0.515 |      0.378 |       0.656 |
| Ear-count channel removed           | Double ML                       | 12.217 |                      0.475 |      0.343 |       0.611 |
| Ear + grain-number channels removed | District x season FE regression |  5.297 |                      0.206 |      0.075 |       0.341 |
| Ear + grain-number channels removed | Double ML                       |  5.669 |                      0.22  |      0.067 |       0.379 |

## B. Formal sensitivity (Cinelli & Hazlett 2020) - district x season FE regression

- Estimate 1.093 t/ha (SE 0.036, OLS); partial R2 of treatment with yield 0.354.
- Robustness value RV = **0.516**: a hidden factor explaining 51.6% of the remaining variation of both treatment and yield would reduce the effect to zero.
- RV (to lose 5% significance) = 0.494.
- RV to bring the estimate down to the ear-calibrated value (53% reduction) = 0.323.

Benchmarks: a hidden factor k times as strong as a measured one.

| benchmark                    |   k_times_as_strong |   r2_with_treatment |   r2_with_yield |   adjusted_effect_t_ha |   adj_ci_low |   adj_ci_high |
|:-----------------------------|--------------------:|--------------------:|----------------:|-----------------------:|-------------:|--------------:|
| Irrigations already given    |                   1 |               0.043 |           0.266 |                  0.932 |        0.871 |         0.993 |
| Irrigations already given    |                   2 |               0.086 |           0.533 |                  0.763 |        0.713 |         0.813 |
| Irrigations already given    |                   3 |               0.129 |           0.803 |                  0.585 |        0.552 |         0.618 |
| Sowing day                   |                   1 |               0.001 |           0.001 |                  1.092 |        1.022 |         1.161 |
| Sowing day                   |                   2 |               0.001 |           0.003 |                  1.09  |        1.021 |         1.16  |
| Sowing day                   |                   3 |               0.002 |           0.004 |                  1.089 |        1.019 |         1.158 |
| Fertiliser practice (8 vars) |                   1 |               0.021 |           0.008 |                  1.074 |        1.004 |         1.144 |
| Fertiliser practice (8 vars) |                   2 |               0.042 |           0.016 |                  1.055 |        0.984 |         1.125 |
| Fertiliser practice (8 vars) |                   3 |               0.063 |           0.023 |                  1.035 |        0.964 |         1.106 |
| District x season (56 cells) |                   1 |               0.204 |           0.306 |                  0.68  |        0.615 |         0.745 |
| District x season (56 cells) |                   2 |               0.408 |           0.682 |                  0.081 |        0.03  |         0.132 |
| District x season (56 cells) |                   3 |               0.613 |           1     |                 -0.763 |       -0.763 |        -0.763 |

## C. District differences vs the impossible ear effect

| District       |   n |   seasons |   yield_pct |   yield_ci_low |   yield_ci_high |   ears_pct |   ears_ci_low |   ears_ci_high |   yield_per_ear_pct |   yield_per_ear_ci_low |   yield_per_ear_ci_high |
|:---------------|----:|----------:|------------:|---------------:|----------------:|-----------:|--------------:|---------------:|--------------------:|-----------------------:|------------------------:|
| Begusarai      | 157 |         6 |        11.4 |            7.4 |            15.6 |        5.4 |           1.7 |            9.3 |                 5.7 |                    0.6 |                    11   |
| Lakhisarai     | 118 |         5 |        14.6 |            9.3 |            20.2 |       11.9 |           3.8 |           20.6 |                 2.4 |                   -6.8 |                    12.5 |
| East Champaran | 108 |         3 |        15.3 |            3.7 |            28.3 |        9.2 |           5.3 |           13.2 |                 5.6 |                   -3.2 |                    15.2 |
| Rohtas         | 171 |         4 |        19.4 |           10.3 |            29.3 |       14.2 |           3   |           26.5 |                 4.6 |                   -8.6 |                    19.7 |
| Buxar          | 225 |         5 |        24.7 |           16.6 |            33.4 |        7.7 |           3.7 |           11.8 |                15.9 |                    7.1 |                    25.3 |
| Muzaffarpur    | 132 |         3 |        39.2 |           26.2 |            53.6 |       38.2 |          15.8 |           64.9 |                 0.7 |                  -10.7 |                    13.7 |
| Kushinagar     | 154 |         6 |        48   |           26.7 |            73   |       26.6 |          10.6 |           44.9 |                16.9 |                   12.4 |                    21.7 |
| Deoria         | 174 |         6 |        58.7 |           45.1 |            73.6 |       24.4 |          15.1 |           34.6 |                27.5 |                   17.2 |                    38.8 |

- Correlation across districts between yield effect and ear 'effect': **0.76**.
