# Agri-Vision - Simulation Stress Test

Semi-synthetic design: 1,810 real plots and covariates, synthetic yields with a KNOWN true effect. 100 repetitions per scenario. Errors are measured against the true average treatment effect (ATE).

Noise calibrated from real control-plot residuals: block x season shock sd 0.20 t/ha, plot noise sd 0.45 t/ha.

## Randomised (k=0) | constant effect
True ATE = 0.800 t/ha

| method                               |   mean_est |   bias |   rmse |   coverage |   ci_width |   mean_reported_se |   empirical_sd |
|:-------------------------------------|-----------:|-------:|-------:|-----------:|-----------:|-------------------:|---------------:|
| 1. Raw difference                    |      0.796 | -0.004 |  0.039 |       0.91 |      0.144 |              0.037 |          0.039 |
| 2. Regression + covariates           |      0.796 | -0.004 |  0.029 |       0.9  |      0.1   |              0.025 |          0.029 |
| 3. Regression + district x season FE |      0.798 | -0.002 |  0.028 |       0.88 |      0.097 |              0.025 |          0.028 |
| 4. Matched-set comparison            |      0.796 | -0.004 |  0.05  |       0.92 |      0.19  |              0.049 |          0.05  |
| 5. Inverse propensity weighting      |      0.791 | -0.009 |  0.032 |       0.98 |      0.168 |              0.043 |          0.031 |
| 6. Doubly robust (AIPW)              |      0.795 | -0.005 |  0.035 |       0.92 |      0.126 |              0.032 |          0.035 |
| 7. Double ML (partially linear)      |      0.784 | -0.016 |  0.034 |       0.84 |      0.102 |              0.026 |          0.03  |

## Mild imbalance (k=0.5) | constant effect
True ATE = 0.800 t/ha

| method                               |   mean_est |   bias |   rmse |   coverage |   ci_width |   mean_reported_se |   empirical_sd |
|:-------------------------------------|-----------:|-------:|-------:|-----------:|-----------:|-------------------:|---------------:|
| 1. Raw difference                    |      0.71  | -0.09  |  0.099 |       0.32 |      0.145 |              0.037 |          0.04  |
| 2. Regression + covariates           |      0.801 |  0.001 |  0.024 |       0.97 |      0.103 |              0.026 |          0.024 |
| 3. Regression + district x season FE |      0.801 |  0.001 |  0.023 |       0.95 |      0.1   |              0.026 |          0.023 |
| 4. Matched-set comparison            |      0.724 | -0.076 |  0.091 |       0.63 |      0.196 |              0.05  |          0.05  |
| 5. Inverse propensity weighting      |      0.802 |  0.002 |  0.035 |       0.98 |      0.184 |              0.047 |          0.035 |
| 6. Doubly robust (AIPW)              |      0.805 |  0.005 |  0.034 |       0.97 |      0.138 |              0.035 |          0.034 |
| 7. Double ML (partially linear)      |      0.789 | -0.011 |  0.031 |       0.9  |      0.108 |              0.028 |          0.03  |

## Real-like imbalance (k=1) | constant effect
True ATE = 0.800 t/ha

| method                               |   mean_est |   bias |   rmse |   coverage |   ci_width |   mean_reported_se |   empirical_sd |
|:-------------------------------------|-----------:|-------:|-------:|-----------:|-----------:|-------------------:|---------------:|
| 1. Raw difference                    |      0.647 | -0.153 |  0.157 |       0.03 |      0.144 |              0.037 |          0.038 |
| 2. Regression + covariates           |      0.803 |  0.003 |  0.03  |       0.93 |      0.109 |              0.028 |          0.03  |
| 3. Regression + district x season FE |      0.802 |  0.002 |  0.03  |       0.93 |      0.106 |              0.027 |          0.03  |
| 4. Matched-set comparison            |      0.667 | -0.133 |  0.144 |       0.32 |      0.205 |              0.052 |          0.053 |
| 5. Inverse propensity weighting      |      0.809 |  0.009 |  0.041 |       0.99 |      0.207 |              0.053 |          0.04  |
| 6. Doubly robust (AIPW)              |      0.808 |  0.008 |  0.044 |       0.95 |      0.155 |              0.04  |          0.043 |
| 7. Double ML (partially linear)      |      0.787 | -0.013 |  0.037 |       0.9  |      0.116 |              0.03  |          0.035 |

## Severe imbalance (k=2) | constant effect
True ATE = 0.800 t/ha

| method                               |   mean_est |   bias |   rmse |   coverage |   ci_width |   mean_reported_se |   empirical_sd |
|:-------------------------------------|-----------:|-------:|-------:|-----------:|-----------:|-------------------:|---------------:|
| 1. Raw difference                    |      0.581 | -0.219 |  0.222 |       0    |      0.142 |              0.036 |          0.037 |
| 2. Regression + covariates           |      0.811 |  0.011 |  0.032 |       0.95 |      0.126 |              0.032 |          0.03  |
| 3. Regression + district x season FE |      0.805 |  0.005 |  0.028 |       0.96 |      0.122 |              0.031 |          0.028 |
| 4. Matched-set comparison            |      0.566 | -0.234 |  0.24  |       0.01 |      0.241 |              0.062 |          0.051 |
| 5. Inverse propensity weighting      |      0.799 | -0.001 |  0.047 |       1    |      0.253 |              0.064 |          0.047 |
| 6. Doubly robust (AIPW)              |      0.801 |  0.001 |  0.047 |       0.98 |      0.186 |              0.048 |          0.047 |
| 7. Double ML (partially linear)      |      0.787 | -0.013 |  0.041 |       0.91 |      0.141 |              0.036 |          0.039 |

## Randomised (k=0) | heterogeneous effect
True ATE = 0.785 t/ha

| method                               |   mean_est |   bias |   rmse |   coverage |   ci_width |   mean_reported_se |   empirical_sd |
|:-------------------------------------|-----------:|-------:|-------:|-----------:|-----------:|-------------------:|---------------:|
| 1. Raw difference                    |      0.785 | -0     |  0.034 |       0.96 |      0.138 |              0.035 |          0.034 |
| 2. Regression + covariates           |      0.785 | -0     |  0.026 |       0.94 |      0.115 |              0.029 |          0.026 |
| 3. Regression + district x season FE |      0.784 | -0.001 |  0.026 |       0.96 |      0.113 |              0.029 |          0.026 |
| 4. Matched-set comparison            |      0.751 | -0.034 |  0.053 |       0.95 |      0.187 |              0.048 |          0.04  |
| 5. Inverse propensity weighting      |      0.787 |  0.002 |  0.033 |       1    |      0.169 |              0.043 |          0.033 |
| 6. Doubly robust (AIPW)              |      0.783 | -0.001 |  0.033 |       0.93 |      0.139 |              0.036 |          0.033 |
| 7. Double ML (partially linear)      |      0.773 | -0.012 |  0.032 |       0.94 |      0.118 |              0.03  |          0.03  |

## Mild imbalance (k=0.5) | heterogeneous effect
True ATE = 0.785 t/ha

| method                               |   mean_est |   bias |   rmse |   coverage |   ci_width |   mean_reported_se |   empirical_sd |
|:-------------------------------------|-----------:|-------:|-------:|-----------:|-----------:|-------------------:|---------------:|
| 1. Raw difference                    |      0.727 | -0.058 |  0.069 |       0.56 |      0.138 |              0.035 |          0.037 |
| 2. Regression + covariates           |      0.791 |  0.006 |  0.029 |       0.97 |      0.118 |              0.03  |          0.028 |
| 3. Regression + district x season FE |      0.791 |  0.006 |  0.028 |       0.98 |      0.116 |              0.029 |          0.027 |
| 4. Matched-set comparison            |      0.702 | -0.083 |  0.092 |       0.62 |      0.191 |              0.049 |          0.04  |
| 5. Inverse propensity weighting      |      0.79  |  0.005 |  0.037 |       0.96 |      0.175 |              0.045 |          0.037 |
| 6. Doubly robust (AIPW)              |      0.787 |  0.002 |  0.04  |       0.94 |      0.146 |              0.037 |          0.04  |
| 7. Double ML (partially linear)      |      0.778 | -0.007 |  0.034 |       0.91 |      0.121 |              0.031 |          0.034 |

## Real-like imbalance (k=1) | heterogeneous effect
True ATE = 0.785 t/ha

| method                               |   mean_est |   bias |   rmse |   coverage |   ci_width |   mean_reported_se |   empirical_sd |
|:-------------------------------------|-----------:|-------:|-------:|-----------:|-----------:|-------------------:|---------------:|
| 1. Raw difference                    |      0.675 | -0.11  |  0.115 |       0.14 |      0.138 |              0.035 |          0.035 |
| 2. Regression + covariates           |      0.794 |  0.009 |  0.031 |       0.95 |      0.123 |              0.031 |          0.03  |
| 3. Regression + district x season FE |      0.795 |  0.01  |  0.03  |       0.94 |      0.121 |              0.031 |          0.028 |
| 4. Matched-set comparison            |      0.666 | -0.119 |  0.128 |       0.39 |      0.208 |              0.053 |          0.048 |
| 5. Inverse propensity weighting      |      0.797 |  0.012 |  0.041 |       0.98 |      0.193 |              0.049 |          0.039 |
| 6. Doubly robust (AIPW)              |      0.785 |  0.001 |  0.039 |       0.98 |      0.163 |              0.042 |          0.039 |
| 7. Double ML (partially linear)      |      0.774 | -0.011 |  0.037 |       0.91 |      0.126 |              0.032 |          0.035 |

## Severe imbalance (k=2) | heterogeneous effect
True ATE = 0.785 t/ha

| method                               |   mean_est |   bias |   rmse |   coverage |   ci_width |   mean_reported_se |   empirical_sd |
|:-------------------------------------|-----------:|-------:|-------:|-----------:|-----------:|-------------------:|---------------:|
| 1. Raw difference                    |      0.625 | -0.16  |  0.164 |       0.01 |      0.137 |              0.035 |          0.036 |
| 2. Regression + covariates           |      0.802 |  0.017 |  0.038 |       0.92 |      0.143 |              0.037 |          0.034 |
| 3. Regression + district x season FE |      0.796 |  0.011 |  0.034 |       0.95 |      0.14  |              0.036 |          0.032 |
| 4. Matched-set comparison            |      0.553 | -0.231 |  0.237 |       0    |      0.241 |              0.062 |          0.05  |
| 5. Inverse propensity weighting      |      0.799 |  0.014 |  0.053 |       1    |      0.239 |              0.061 |          0.051 |
| 6. Doubly robust (AIPW)              |      0.793 |  0.008 |  0.055 |       0.94 |      0.198 |              0.05  |          0.055 |
| 7. Double ML (partially linear)      |      0.781 | -0.004 |  0.045 |       0.9  |      0.15  |              0.038 |          0.045 |

## Actual trial assignment | heterogeneous effect
True ATE = 0.785 t/ha

| method                               |   mean_est |   bias |   rmse |   coverage |   ci_width |   mean_reported_se |   empirical_sd |
|:-------------------------------------|-----------:|-------:|-------:|-----------:|-----------:|-------------------:|---------------:|
| 1. Raw difference                    |      0.685 | -0.1   |  0.105 |       0.18 |      0.137 |              0.035 |          0.033 |
| 2. Regression + covariates           |      0.833 |  0.048 |  0.056 |       0.83 |      0.152 |              0.039 |          0.03  |
| 3. Regression + district x season FE |      0.827 |  0.042 |  0.051 |       0.89 |      0.153 |              0.039 |          0.029 |
| 4. Matched-set comparison            |      0.669 | -0.116 |  0.122 |       0.7  |      0.272 |              0.069 |          0.039 |
| 5. Inverse propensity weighting      |      0.857 |  0.072 |  0.092 |       0.99 |      0.31  |              0.079 |          0.057 |
| 6. Doubly robust (AIPW)              |      0.844 |  0.059 |  0.096 |       0.95 |      0.304 |              0.078 |          0.076 |
| 7. Double ML (partially linear)      |      0.808 |  0.023 |  0.046 |       0.93 |      0.169 |              0.043 |          0.04  |

## Actual assignment + hidden confounder | heterogeneous effect
True ATE = 0.785 t/ha

| method                               |   mean_est |   bias |   rmse |   coverage |   ci_width |   mean_reported_se |   empirical_sd |
|:-------------------------------------|-----------:|-------:|-------:|-----------:|-----------:|-------------------:|---------------:|
| 1. Raw difference                    |      0.885 |  0.1   |  0.104 |       0.13 |      0.142 |              0.036 |          0.027 |
| 2. Regression + covariates           |      1.033 |  0.248 |  0.25  |       0    |      0.158 |              0.04  |          0.026 |
| 3. Regression + district x season FE |      1.029 |  0.244 |  0.245 |       0    |      0.158 |              0.04  |          0.026 |
| 4. Matched-set comparison            |      0.866 |  0.081 |  0.09  |       0.91 |      0.281 |              0.072 |          0.041 |
| 5. Inverse propensity weighting      |      1.06  |  0.275 |  0.281 |       0    |      0.312 |              0.08  |          0.056 |
| 6. Doubly robust (AIPW)              |      1.049 |  0.264 |  0.273 |       0.03 |      0.3   |              0.077 |          0.069 |
| 7. Double ML (partially linear)      |      1.011 |  0.226 |  0.23  |       0    |      0.181 |              0.046 |          0.043 |

## Overall ranking (mean over all scenarios)

| method                               |   rmse |   cov_gap |
|:-------------------------------------|-------:|----------:|
| 3. Regression + district x season FE |  0.052 |     0.116 |
| 2. Regression + covariates           |  0.055 |     0.122 |
| 7. Double ML (partially linear)      |  0.057 |     0.136 |
| 5. Inverse propensity weighting      |  0.069 |     0.128 |
| 6. Doubly robust (AIPW)              |  0.07  |     0.107 |
| 1. Raw difference                    |  0.111 |     0.628 |
| 4. Matched-set comparison            |  0.125 |     0.405 |
