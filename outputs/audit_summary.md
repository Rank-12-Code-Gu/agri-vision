# Agri-Vision - Data Audit Summary

## 1. Overview
- Plots: **1810** (control 1050, treatment 760; treated share 42.0%)
- Seasons: 6 (2016-17, 2017-18, 2018-19, 2019-20, 2020-21, 2021-22)
- Districts: 10; blocks: 97; villages: 223
- Exact duplicate rows: 0

## 2. Treatment imbalance
By season:

| Year    |   Control |   Treatment |   TreatedShare |
|:--------|----------:|------------:|---------------:|
| 2016-17 |       120 |          38 |          0.241 |
| 2017-18 |       219 |         169 |          0.436 |
| 2018-19 |       187 |         247 |          0.569 |
| 2019-20 |       313 |         189 |          0.376 |
| 2020-21 |        92 |          64 |          0.41  |
| 2021-22 |       119 |          53 |          0.308 |

By district:

| District       |   Control |   Treatment |   TreatedShare |
|:---------------|----------:|------------:|---------------:|
| Muzaffarpur    |       144 |          42 |          0.226 |
| Madhepura      |       160 |          50 |          0.238 |
| Rohtas         |       118 |          72 |          0.379 |
| East Champaran |       100 |          73 |          0.422 |
| Bhojpur        |       118 |          95 |          0.446 |
| Begusarai      |        85 |          72 |          0.459 |
| Lakhisarai     |        68 |          60 |          0.469 |
| Kushinagar     |        76 |          78 |          0.506 |
| Deoria         |        83 |          91 |          0.523 |
| Buxar          |        98 |         127 |          0.564 |

- Treated share ranges from 23% to 56% across districts and 24% to 57% across seasons.
- District x season cells with no plots: 4 of 60.

## 3. Study design: is it a paired trial?
Plots were grouped into 'match sets' = same season, block, village, sowing date, variety and tillage (the closest available proxy for 'same farmer', since farmer IDs are anonymised).
- Match sets: 1232; sets containing both arms: **189** (504 plots, 28% of data).
- Plots with no comparable plot of the other arm: 1306 (72%).
- Conclusion: the data behave mostly like **unpaired, voluntarily assigned** plots, so simple averages can be confounded by place, season and practice.

## 4. Data-quality checks and cleaning decisions
- Dropped FarmerName and MobileNumber (anonymised placeholders).
- Harmonised SoilType case ('medium' -> 'Medium', 'light' -> 'Light').
- Harmonised PreviousCrop ('Paddy'/'paddy'/'rice' -> 'Rice', case fixed).
- Grouped varieties with <10 plots into 'Other'.
- Irrigation events match arm for every plot (control = base, treatment = base + 1).
- 36 control plots carry a DateofAdditionalIrrigation but no extra irrigation event; kept as controls and flagged (likely data-entry).
- Missing BasalDAP/BasalNPK/BasalZn/Split3Urea treated as 'not applied' (0 + usage flag).
- Of the flagged control dates, 6 have an impossible month for a wheat season (e.g. '2022.10.03'), suggesting day/month swaps.
- Grain yield range 1.7-6.7 t/ha; grain > biomass in 0 plots.
- Extreme yield outliers (beyond 3x IQR): 0.

Missing values in the raw file (share of rows):

|                            |   missing_share |
|:---------------------------|----------------:|
| FifthIrrigationDay         |           0.984 |
| BasalNPK                   |           0.795 |
| GradeNPK                   |           0.795 |
| FourthIrrigationDay        |           0.707 |
| BasalZn                    |           0.702 |
| Split3Urea                 |           0.659 |
| DateofAdditionalIrrigation |           0.56  |
| ThirdIrrigationDay         |           0.2   |
| BasalDAP                   |           0.187 |
| SecondIrrigationDay        |           0.029 |

Post-treatment variables (lodging, biomass, test weight, tillers, grains, harvest date) are **excluded** from adjustment, because the extra irrigation can change them.

## 5. Are treatment and control plots comparable before treatment?
Standardised mean difference (SMD): |SMD| > 0.10 means the groups differ.

- Covariates with |SMD| > 0.10: **24 of 44**.

| covariate            |   SMD_raw |
|:---------------------|----------:|
| BaseIrrigations      |    -0.468 |
| Year=2018-19         |     0.344 |
| VarietyGrp=HD2967    |     0.337 |
| Longitude            |    -0.285 |
| District=Madhepura   |    -0.28  |
| District=Muzaffarpur |    -0.28  |
| Year=2016-17         |    -0.236 |
| VarietyGrp=DBW187    |    -0.228 |
| LandType=Medium Land |     0.224 |
| District=Buxar       |     0.221 |
| UsedZn               |     0.216 |
| Split1Urea           |    -0.216 |
| VarietyGrp=HD2733    |    -0.208 |
| Split3Urea_f         |     0.166 |
| SoilType=Light       |    -0.163 |
| LandType=Lowland     |    -0.154 |
| Year=2021-22         |    -0.152 |
| LandType=Upland      |    -0.143 |
| District=Deoria      |     0.136 |
| ZeroTillage          |     0.119 |
| Year=2019-20         |    -0.111 |
| District=Kushinagar  |     0.107 |
| PrevCropResidue      |     0.107 |
| VarietyGrp=Other     |    -0.105 |

## 6. Outcome: grain yield (t/ha), unadjusted
| Treated   |   count |   mean |   std |   min |   25% |   50% |   75% |   max |
|:----------|--------:|-------:|------:|------:|------:|------:|------:|------:|
| Control   |    1050 |   3.89 |  0.82 |   1.7 |   3.3 |   3.9 |   4.5 |   6.7 |
| Treatment |     760 |   4.8  |  0.87 |   2.1 |   4.3 |   4.8 |   5.4 |   6.7 |

- Raw difference: **+0.916 t/ha** (+23.6%). This is NOT a causal estimate; see baselines.
