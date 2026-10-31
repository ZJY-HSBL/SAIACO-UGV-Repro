# v0.2.0 — Reproduction audit and ablations / 复现审计和消融

- Repaired the turn-count metric for collinear but unequal segment lengths.
- Added a deterministic Dijkstra 8-neighbor graph shortest-path oracle (and a feasible waypoint-shortcut comparison).
- Digitized 6 complex 30×30 obstacle layouts from the paper's published figures. The starts/goals are **assumed evaluation probes**, not confirmed original endpoints.
- Executed 42 trials: 2 main maps × 4 conditions × 3 seeds, plus 6 special maps × 3 seeds; 12 ants and 20 iterations per trial.
- Complete hybrid mean length (three seeds): 20×20 **28.43**; 30×30 **48.41**.
- No-smoothing mean length: 20×20 **35.75**; 30×30 **58.08**.
- Added 18 automated tests, per-seed CSV results, Dijkstra benchmarks and figures in README.

**Scientific interpretation:** Preliminary exploration only. Differences from the paper are still substantial on the 30×30 map; smoothing accounts for most observed path-length gains. SA and direction guidance have not demonstrated consistent added value in this limited test. Original author maps and missing parameter values have not been obtained.

Original research: Zhu and Yu, *Electronic Science and Technology*, DOI 10.16180/j.cnki.issn1007-7820.2027.05.003.
