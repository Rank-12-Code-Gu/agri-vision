# Agri-Vision: Causal Decision Engine for Targeted Wheat Irrigation

Final-year B.Tech CSE project (ADTU). Question: how much does one extra irrigation at
grain filling raise wheat yield, how reliably can we estimate it from imbalanced
farmer-managed trials, and which farms benefit most?

## Data
Singh, M., Patra, S., Ajay, A., et al. (2023). *Large on-farm trial data to assess the
effect of additional irrigation on yields of wheat established through zero and
conventional tillage methods in eastern India*. CIMMYT Research Data & Software
Repository Network, V3.1. hdl:11529/10548945

Files are in `data/raw/` (downloaded from the repository API; MD5 checksums verified).

## Reproduce
```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python scripts/02_full_audit.py   # data audit + figures 01-05
.venv/Scripts/python scripts/03_baselines.py    # 7 estimators + diagnostics, figures 06-08 (~2 min)
.venv/Scripts/python scripts/04_simulation.py --reps 100  # simulation stress test, figures 09-11 (~15 min)
.venv/Scripts/python scripts/05_who_benefits.py         # causal forest, figures 12-17, saves models/ (~1 min)
.venv/Scripts/python scripts/06_weather_test.py        # NASA POWER weather test, figures 18-20 (~5 min; internet on first run)
.venv/Scripts/python scripts/07_sensitivity.py         # negative controls + sensemakr bounds, figures 21-23 (~1.5 min)
.venv/Scripts/python scripts/08_build_advisor.py       # models for the dashboard (~40 s)
.venv/Scripts/python -m streamlit run app/app.py         # open the dashboard at http://localhost:8501
```

## Layout
- `src/agrivision/data.py`: loading, cleaning (logged), pre-treatment covariates
- `src/agrivision/estimators.py`: raw difference, regression, fixed effects, matched sets,
  IPW, AIPW, Double ML (cluster-robust SEs by block x season)
- `outputs/audit_summary.md`, `outputs/baselines_summary.md`: auto-generated reports
- `outputs/figures/`, `outputs/tables/`: charts and CSV tables

## Status
- [x] Data audit
- [x] Baseline estimators
- [x] Simulation stress test (`scripts/04_simulation.py --reps 100`, ~15 min; findings in `outputs/simulation_findings.md`)
- [x] Heterogeneous effects (causal forest), validation, priority targeting (`scripts/05_who_benefits.py`; findings in `outputs/who_benefits_findings.md`)
- [x] Weather test: grain-filling heat (NASA POWER) does not explain who benefits; district does (`scripts/06_weather_test.py`; findings in `outputs/weather_test_findings.md`)
- [x] Sensitivity: yield-component negative control reveals hidden confounding; corrected effect ~0.2-0.5 t/ha (`scripts/07_sensitivity.py`; findings in `outputs/sensitivity_findings.md`)
- [x] Dashboard: Streamlit Irrigation Decision Assistant with corrected effects (`app/app.py`, models from `scripts/08_build_advisor.py`)

## Presentation material
- `poster/AgriVision_Poster.pptx` (+ `.pdf`, `.png`): e-poster on the university template, built by `poster/build_poster.py`
- `docs/Panel_Prep_Guide.md`: plain-language explanation, key numbers and likely panel Q&A
