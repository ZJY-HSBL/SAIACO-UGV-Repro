# v0.1.0 — Initial Independent Reproduction

Initial tested source implementation of the core Zhu & Yu (2026) SA-IACO path-planning method (DOI 10.16180/j.cnki.issn1007-7820.2027.05.003).

- Classical ACO; improved direction-guided ACO; SA-IACO with four-neighbor A* initialization.
- Adaptive-density waypoint elimination with conservative obstacle collision checking.
- Digitized **approximate** 20×20 and 30×30 experimental maps; illustrative U and X mazes.
- Reproducible script: 30 ants, 60 iterations, random seed 2026; pytest suite.
- Comparative metrics and generated PNG/CSV/JSON experimental outputs.

**Limitations:** This is an independent partial numerical reproduction. The paper does not disclose its original maps and several essential parameter values. The reproduced performance metrics differ materially from the paper, particularly in the 30×30 case. This release does not contain original author code.
