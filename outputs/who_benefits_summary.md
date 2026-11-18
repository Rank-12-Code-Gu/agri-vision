# Agri-Vision - Who Benefits? (causal forest)

Model: CausalForestDML (econml), 2,000 honest trees, gradient-boosting nuisance models, 5-fold cross-fitting grouped by block x season.
Effect modifiers: SowingDay, BaseIrrigations, ZeroTillage, District, SoilType, LandType, VarietyGrp.
Controls only: season, fertiliser, seed rate, residue, GPS, weeding, previous crop.

## Average effect

- Forest ATE: **+0.889 t/ha** (95% CI +0.788 to +0.990).
- Predicted plot-level gain ranges 0.50 to 1.80 t/ha (10th-90th percentile 0.61 to 1.39).

## Is the heterogeneity real? (out-of-fold validation)

- Calibration slope (BLP): **0.82** (SE 0.25, p = 0.00116). 1 = predictions perfectly calibrated; 0 = no real heterogeneity detected.
- Top-quintile minus bottom-quintile measured gain: **+0.563 t/ha** (SE 0.229, p = 0.0138).

| group   |   pred_mean |   dr_effect |    se |   ci_low |   ci_high |   n |
|:--------|------------:|------------:|------:|---------:|----------:|----:|
| Q1      |       0.637 |       0.698 | 0.095 |    0.511 |     0.885 | 365 |
| Q2      |       0.78  |       0.823 | 0.1   |    0.628 |     1.018 | 360 |
| Q3      |       0.884 |       1.021 | 0.144 |    0.739 |     1.302 | 362 |
| Q4      |       1.001 |       1.015 | 0.194 |    0.636 |     1.395 | 363 |
| Q5      |       1.394 |       1.262 | 0.206 |    0.859 |     1.665 | 360 |

## Effect by farm group (doubly robust, cluster-robust 95% CI)

| factor                                         | level          |    n |   n_treated |   dr_effect |   ci_low |   ci_high |   forest_mean |
|:-----------------------------------------------|:---------------|-----:|------------:|------------:|---------:|----------:|--------------:|
| Irrigations already given by farmer            | 1              |  142 |          90 |       0.974 |    0.67  |     1.277 |         0.839 |
| Irrigations already given by farmer            | 2              |  476 |         256 |       0.722 |    0.537 |     0.906 |         0.772 |
| Irrigations already given by farmer            | 3              | 1047 |         385 |       1.143 |    0.855 |     1.432 |         1.132 |
| Irrigations already given by farmer            | 4              |  145 |          29 |       0.446 |    0.122 |     0.77  |         0.721 |
| Sowing window                                  | Early Sown     | 1567 |         661 |       0.988 |    0.8   |     1.176 |         0.992 |
| Sowing window                                  | Late Sown      |  243 |          99 |       0.803 |    0.42  |     1.187 |         0.91  |
| Tillage (ZT = zero tillage, CT = conventional) | CT             |  747 |         288 |       0.997 |    0.776 |     1.217 |         0.948 |
| Tillage (ZT = zero tillage, CT = conventional) | ZT             | 1063 |         472 |       0.94  |    0.739 |     1.14  |         1.004 |
| Soil type                                      | Heavy          |  367 |         155 |       0.856 |    0.657 |     1.054 |         0.77  |
| Soil type                                      | Light          |   41 |           7 |       0.918 |    0.721 |     1.114 |         0.973 |
| Soil type                                      | Medium         | 1402 |         598 |       0.993 |    0.771 |     1.214 |         1.037 |
| Land type                                      | Lowland        |  369 |         128 |       1.031 |    0.87  |     1.192 |         0.95  |
| Land type                                      | Medium Land    | 1291 |         586 |       0.977 |    0.777 |     1.177 |         1.004 |
| Land type                                      | Upland         |  150 |          46 |       0.678 |    0.111 |     1.245 |         0.864 |
| District                                       | Begusarai      |  157 |          72 |       0.49  |    0.306 |     0.673 |         0.618 |
| District                                       | Bhojpur        |  213 |          95 |       1.37  |    1.165 |     1.575 |         1.153 |
| District                                       | Buxar          |  225 |         127 |       0.954 |    0.708 |     1.2   |         0.84  |
| District                                       | Deoria         |  174 |          91 |       1.889 |    1.491 |     2.286 |         1.783 |
| District                                       | East Champaran |  173 |          73 |       0.51  |    0.258 |     0.762 |         0.79  |
| District                                       | Kushinagar     |  154 |          78 |       1.229 |    0.696 |     1.762 |         1.302 |
| District                                       | Lakhisarai     |  128 |          60 |      -0.168 |   -1.426 |     1.091 |         0.693 |
| District                                       | Madhepura      |  210 |          50 |       1.033 |    0.888 |     1.178 |         0.839 |
| District                                       | Muzaffarpur    |  186 |          42 |       1.077 |    0.753 |     1.4   |         1.034 |
| District                                       | Rohtas         |  190 |          72 |       0.832 |    0.689 |     0.976 |         0.736 |

## What drives the differences (forest importance)

|                 |   importance |
|:----------------|-------------:|
| District        |        0.866 |
| BaseIrrigations |        0.085 |
| SowingDay       |        0.027 |
| ZeroTillage     |        0.013 |
| SoilType        |        0.004 |
| LandType        |        0.003 |
| VarietyGrp      |        0.002 |

## Economics (assumptions in src/agrivision/economics.py - verify)

- Wheat price Rs 2425/quintal; irrigation cost Rs 2500/ha -> break-even gain **0.103 t/ha**.
- Plots whose predicted gain exceeds break-even: 100.0%; whose 95% lower bound exceeds it: 100.0%.
- Median net benefit: Rs 19,701/ha.

## If water/diesel is limited: priority targeting

|   share_irrigated |   gain_targeted |   gain_random |   share_of_full_gain_captured |
|------------------:|----------------:|--------------:|------------------------------:|
|              0.25 |           0.293 |         0.241 |                         0.304 |
|              0.5  |           0.57  |         0.482 |                         0.592 |
|              0.75 |           0.783 |         0.722 |                         0.813 |

## Simple readable rule (depth-2 tree fitted to forest predictions)

```
|--- BaseIrrigations <= 2.50
|   |--- SowingDay <= 322.50
|   |   |--- value: [0.84]
|   |--- SowingDay >  322.50
|   |   |--- value: [0.66]
|--- BaseIrrigations >  2.50
|   |--- SoilType=Heavy <= 0.50
|   |   |--- value: [1.13]
|   |--- SoilType=Heavy >  0.50
|   |   |--- value: [0.81]

```
