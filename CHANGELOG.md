# Changelog

## [v0.3.0] — 2026-10-31

- Separated the ant-choice and Metropolis RNG streams to remove paired-ablation confounding; 20 tests.
- Identified absent SA-to-pheromone feedback in the original paper-inspired implementation.
- Added optional **non-paper** elite-deposit reinforcement with `elite_deposit_weight=3.0` for exploratory comparison.
- Executed 360 paired trials: two reconstructed maps × 30 seeds × six configurations; retained data, uncertainty intervals, figure plots, and map SHA-256 hashes.
- Main result: SA enabled/disabled are identical without pheromone feedback; smoothing supplies the dominant length reduction.
- Numerical match to the source paper remains unresolved.

# Changelog

## [v0.2.0] — 2026-10-31

- Corrected direction-change turn counting for unequal collinear segments.
- Added exact 8-neighbor Dijkstra graph-distance oracle and feasible shortcut reference.
- Added approximate obstacle grids reconstructed from Figures 11–16; assumed test endpoints are explicitly identified.
- Added 3-seed paired ablations (SA, direction, smoothing), raw-search vs smoothing contributions, metrics CSV/JSON and plots.
- Added automated workflow to rerun the experiments and publish the source and evidence as a GitHub Release.
- Limitation: three seeds and incomplete author-side parameters do NOT establish exact numerical reproduction or significance.

## [v0.1.0] — 2026-10-30

Initial independent implementation of Zhu & Yu (2026), DOI 10.16180/j.cnki.issn1007-7820.2027.05.003.

- Implemented four-neighbor A*, classic ACO, improved ACO, simulated annealing and dynamic waypoint smoothing.
- Reconstructed 20×20 and 30×30 grids from paper figures and documented missing author-side details.
- Added test suite, CLI, plotting, metrics and figure generation.
- Benchmarked with 30 ants × 60 iterations, seed 2026.
- Added bilingual research README and GitHub Actions.

**Scientific limitation:** Not an exact numerical reproduction; figure digitization and unspecified hyperparameters introduce substantial discrepancies.
