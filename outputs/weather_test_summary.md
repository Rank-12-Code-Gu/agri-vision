# Agri-Vision - Weather Test: does grain-filling heat explain who benefits?

Weather: NASA POWER daily (MERRA-2), 25 grid cells. Grain-filling window = 95-125 days after each plot's sowing date; heat day = Tmax > 34 C. Effect measured with doubly robust scores; SEs clustered by district x season (the level at which weather varies).

## 1. Where does weather vary?

|             |   share_explained_by_season |   share_explained_by_district |
|:------------|----------------------------:|------------------------------:|
| GF_HeatDays |                       0.752 |                         0.035 |
| GF_RainMM   |                       0.762 |                         0.124 |
| GF_TmaxMean |                       0.73  |                         0.029 |

Season-by-season means:

| Year    |   GF_TmaxMean |   GF_HeatDays |   GF_RainMM |
|:--------|--------------:|--------------:|------------:|
| 2016-17 |         32.26 |          7.77 |        7.17 |
| 2017-18 |         35.07 |         21.61 |        2.98 |
| 2018-19 |         32.77 |         12.75 |       10.4  |
| 2019-20 |         29.05 |          1.16 |       64.92 |
| 2020-21 |         34.71 |         19.88 |        1.95 |
| 2021-22 |         30.67 |          5.98 |        2.83 |

## 2. Does weather change the effect? (per 1 SD of the weather variable)

| model                                       | term          |   coef_t_per_ha_per_SD |   ci_low |   ci_high |     p |
|:--------------------------------------------|:--------------|-----------------------:|---------:|----------:|------:|
| heat days only                              | GF_HeatDays_z |                 -0.035 |   -0.19  |     0.119 | 0.653 |
| heat days + rain                            | GF_HeatDays_z |                  0.015 |   -0.145 |     0.175 | 0.857 |
| heat days + rain                            | GF_RainMM_z   |                  0.082 |   -0.047 |     0.211 | 0.211 |
| mean Tmax + rain                            | GF_TmaxMean_z |                 -0.013 |   -0.176 |     0.149 | 0.871 |
| mean Tmax + rain                            | GF_RainMM_z   |                  0.065 |   -0.064 |     0.194 | 0.324 |
| district FE + heat + rain (within district) | GF_HeatDays_z |                  0.001 |   -0.113 |     0.116 | 0.983 |
| district FE + heat + rain (within district) | GF_RainMM_z   |                  0.05  |   -0.059 |     0.158 | 0.37  |

- 1 SD = 9.1 heat days; 30.5 mm rain.

## 3. Do weather differences explain the district differences?

- Spread (SD) of district effects: 0.539 t/ha without weather -> 0.536 with heat + rain.
- District effects still jointly significant after adding weather: p = 5.15e-43.
- Weather jointly significant after district: p = 0.582.
- R2 of effect scores: district 0.078, season 0.015, heat+rain 0.002, district+heat+rain 0.078.

### District cross-check (within-season regression per district, practice-adjusted)

| District       |   n |   seasons |   within_season_effect |   ci_low |   ci_high |   dr_score_mean |
|:---------------|----:|----------:|-----------------------:|---------:|----------:|----------------:|
| Madhepura      | 120 |         2 |                 -8.736 |  -25.135 |     7.663 |           1.033 |
| Begusarai      | 157 |         6 |                  0.461 |    0.276 |     0.646 |           0.49  |
| East Champaran | 108 |         3 |                  0.568 |    0.2   |     0.936 |           0.51  |
| Lakhisarai     | 118 |         5 |                  0.586 |    0.393 |     0.779 |          -0.168 |
| Rohtas         | 171 |         4 |                  0.637 |    0.311 |     0.963 |           0.832 |
| Bhojpur        | 136 |         2 |                  0.947 |   -0.238 |     2.131 |           1.37  |
| Buxar          | 225 |         5 |                  0.968 |    0.693 |     1.244 |           0.954 |
| Muzaffarpur    | 132 |         3 |                  1.316 |    0.932 |     1.7   |           1.077 |
| Kushinagar     | 154 |         6 |                  1.623 |    1.09  |     2.155 |           1.229 |
| Deoria         | 174 |         6 |                  1.866 |    1.517 |     2.215 |           1.889 |

## 4. Robustness to window and threshold

| window_DAS   |   threshold_C |   heat_coef |   heat_p |   rain_coef |   rain_p |
|:-------------|--------------:|------------:|---------:|------------:|---------:|
| 85-115       |            32 |      -0.062 |    0.435 |      -0.006 |    0.956 |
| 85-115       |            34 |       0.022 |    0.746 |       0.041 |    0.703 |
| 85-115       |            36 |       0.023 |    0.695 |       0.037 |    0.717 |
| 95-125       |            32 |      -0.01  |    0.914 |       0.067 |    0.354 |
| 95-125       |            34 |       0.015 |    0.857 |       0.082 |    0.211 |
| 95-125       |            36 |       0.012 |    0.868 |       0.079 |    0.208 |
| 105-135      |            32 |      -0.003 |    0.977 |       0.074 |    0.313 |
| 105-135      |            34 |      -0.013 |    0.877 |       0.067 |    0.276 |
| 105-135      |            36 |      -0.02  |    0.831 |       0.064 |    0.27  |

## 5. Causal-forest comparison (out-of-fold calibration)

| model                         | validation   |   calibration_slope |   slope_se |   slope_p |   top_minus_bottom_quintile |
|:------------------------------|:-------------|--------------------:|-----------:|----------:|----------------------------:|
| Practice only                 | new locality |               0.2   |      0.597 |     0.737 |                      -0.059 |
| Practice only                 | new season   |              -0.047 |      0.473 |     0.92  |                       0.03  |
| District + practice           | new locality |               0.817 |      0.306 |     0.008 |                       0.568 |
| District + practice           | new season   |               0.798 |      0.24  |     0.001 |                       0.738 |
| Weather + practice            | new locality |               0.888 |      0.373 |     0.017 |                       0.512 |
| Weather + practice            | new season   |              -0.093 |      0.8   |     0.907 |                      -0.007 |
| District + weather + practice | new locality |               0.795 |      0.381 |     0.037 |                       0.576 |
| District + weather + practice | new season   |               0.739 |      0.366 |     0.043 |                       0.647 |

## District-season cells used in Figure 18

| District       | Year    |   n |   share |   effect |   heat |   rain |
|:---------------|:--------|----:|--------:|---------:|-------:|-------:|
| Begusarai      | 2016-17 |  15 |    0.07 |     0.73 |   7.27 |   9.27 |
| Begusarai      | 2017-18 |  30 |    0.5  |     0.59 |  20.33 |   0.48 |
| Begusarai      | 2018-19 |  40 |    0.5  |     0.41 |  17.65 |  15.12 |
| Begusarai      | 2019-20 |  24 |    0.5  |     0.06 |  10.5  |  61.23 |
| Begusarai      | 2020-21 |  28 |    0.5  |     0.48 |  20.71 |   0.56 |
| Begusarai      | 2021-22 |  20 |    0.5  |     0.85 |   5.15 |  13.1  |
| Bhojpur        | 2017-18 |  72 |    0.53 |     1.4  |  23.15 |   0.48 |
| Bhojpur        | 2019-20 |  64 |    0.25 |     1.41 |   0    |  55.35 |
| Buxar          | 2016-17 |  18 |    0.33 |     0.19 |   9.44 |   3.39 |
| Buxar          | 2017-18 |  48 |    0.6  |     1.22 |  23.19 |   0.57 |
| Buxar          | 2018-19 |  60 |    0.82 |     1.16 |  13.45 |   4.31 |
| Buxar          | 2019-20 |  80 |    0.5  |     0.69 |   0    |  51.46 |
| Buxar          | 2021-22 |  19 |    0.16 |     1.46 |   9.05 |   1.49 |
| Deoria         | 2016-17 |  14 |    0.5  |     1.15 |   6    |   5.98 |
| Deoria         | 2017-18 |  40 |    0.6  |     1.96 |  23.4  |   0.37 |
| Deoria         | 2018-19 |  40 |    0.5  |     1.74 |   7.5  |  12.11 |
| Deoria         | 2019-20 |  40 |    0.5  |     2.59 |   1.9  |  56.54 |
| Deoria         | 2020-21 |  20 |    0.5  |     2.52 |  23.9  |   1.34 |
| Deoria         | 2021-22 |  20 |    0.5  |     0.53 |   7.65 |   0.47 |
| East Champaran | 2017-18 |  40 |    0.5  |     0.75 |  23.2  |   2.62 |
| East Champaran | 2018-19 |  40 |    0.95 |     0.59 |  12.4  |  13.71 |
| East Champaran | 2019-20 |  28 |    0.54 |     0.44 |   0.5  |  45.67 |
| Kushinagar     | 2016-17 |  16 |    0.5  |     0.7  |   6    |   8.91 |
| Kushinagar     | 2017-18 |  20 |    0.5  |     1.3  |  21.35 |   1.25 |
| Kushinagar     | 2018-19 |  40 |    0.5  |     0.51 |  14.08 |   8.5  |
| Kushinagar     | 2019-20 |  38 |    0.53 |     2.02 |   2    |  56.3  |
| Kushinagar     | 2020-21 |  20 |    0.5  |     1.33 |  23.5  |   1.54 |
| Kushinagar     | 2021-22 |  20 |    0.5  |     1.41 |   4.55 |   0.44 |
| Lakhisarai     | 2017-18 |  20 |    0.5  |     0.83 |  17.9  |   0.69 |
| Lakhisarai     | 2018-19 |  38 |    0.53 |    -2.21 |  12.11 |  16.79 |
| Lakhisarai     | 2019-20 |  20 |    0.5  |     0.57 |   0.3  |  41.06 |
| Lakhisarai     | 2020-21 |  20 |    0.5  |     0.73 |  18.4  |   1.61 |
| Lakhisarai     | 2021-22 |  20 |    0.5  |     0.81 |   4.1  |   2.74 |
| Madhepura      | 2019-20 |  80 |    0.25 |     1.11 |   0.18 | 110.81 |
| Madhepura      | 2020-21 |  40 |    0.5  |     0.54 |  16.62 |   4.01 |
| Muzaffarpur    | 2016-17 |  18 |    0.28 |     1.27 |   9.89 |  10.53 |
| Muzaffarpur    | 2018-19 |  34 |    0.5  |     0.46 |  12.26 |  12.21 |
| Muzaffarpur    | 2019-20 |  80 |    0.25 |     1.41 |   1.65 |  57.94 |
| Rohtas         | 2016-17 |  22 |    0.5  |     0.66 |   7.27 |   5.26 |
| Rohtas         | 2017-18 |  40 |    0.57 |     0.65 |  20    |   1.32 |
| Rohtas         | 2018-19 |  61 |    0.36 |     0.95 |  11.74 |   7.15 |
| Rohtas         | 2019-20 |  48 |    0.33 |     0.86 |   0.23 |  72.13 |
