# Changelog

## [v0.1.0] — 2026-10-30

Initial independent implementation of Zhu & Yu (2026), DOI 10.16180/j.cnki.issn1007-7820.2027.05.003.

- Implemented four-neighbor A*, classic ACO, improved ACO, simulated annealing and dynamic waypoint smoothing.
- Reconstructed 20×20 and 30×30 grids from paper figures and documented missing author-side details.
- Added test suite, CLI, plotting, metrics and figure generation.
- Benchmarked with 30 ants × 60 iterations, seed 2026.
- Added bilingual research README and GitHub Actions.

**Scientific limitation:** Not an exact numerical reproduction; figure digitization and unspecified hyperparameters introduce substantial discrepancies.
