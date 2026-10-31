# v0.3.0 — RNG isolation, independent-seed validation / 独立随机数实验

Research continuation based on Zhu & Yu (2026), *Electronic Science and Technology*, DOI 10.16180/j.cnki.issn1007-7820.2027.05.003.

- **20 pytest checks** (after RNG isolation and nonpaper feedback tests); Python 3.10/3.12 CI.
- **360 independent paired runs**: 2 reconstructed figure grids × 30 seeds × 6 conditions, 10 ants, 15 iterations.
- **Full SA-IACO final lengths:** 20×20 mean 28.2672, 30×30 mean 48.6607.
- **No-SA results exactly match full SA** in both grids for all 30 paired seeds because SA state was not used in pheromone reinforcement.
- **No-direction** mean final length: 27.5192 / 48.3951; **no-smoothing**: 35.2162 / 57.7752.
- Optional **nonpaper research extension** `elite_deposit_weight=3.0` to reinforce the SA-selected route; no confirmed statistically robust benefit on both maps.
- Reproducible `scripts/study_v03.py`; CI-published `outputs/study_v03/runs.csv`, paired bootstrap CIs and visualizations.
- The study retains the original scientific caveat: source authors did not provide complete hyperparameters or map matrices. **Not an exact reproduction**.

For details see README section 7 and evidence CSV in `outputs/study_v03`.
