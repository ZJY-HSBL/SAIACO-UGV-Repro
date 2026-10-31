# v0.4.0 — Held-out validation and SA mechanism diagnostics

Research basis: Zhu Zixuan & Yu Lianzhi, *Electronic Science and Technology* (2026), DOI 10.16180/j.cnki.issn1007-7820.2027.05.003.

**Independent held-out experiment:** 480 runs = 8 approximate paper-figure maps × 20 unused paired seeds (2000–2019) × 3 variants; 10 ants, 15 iterations and fixed elite pheromone coefficient 3.0. Six special maze endpoints are reconstruction assumptions.

**Two prespecified comparisons** (relative length reduction, higher is better):
- **Elite SA vs elite greedy:** +0.06484%, paired bootstrap 95% CI [−0.15149%, +0.29100%], Holm-adjusted sign-test p=0.53369.
- **Elite SA vs original paper-inspired implementation:** +0.47866%, CI [−0.00254%, +0.95946%], adjusted p=0.53369.

**Conclusion:** Neither primary hypothesis demonstrates a statistically reliable improvement. Higher-score Metropolis acceptance is measurable, but not sufficient to guarantee shorter routes. Figure-digitized maps and incomplete original parameter disclosure prevent claims of strict numerical reproduction.

**Technical changes:** SA acceptance diagnostics, held-out paired analysis clustered by seed (avoids map-level pseudoreplication), exact sign tests with Holm adjustment, collision checks, Dijkstra raw-path reference, complete CSV and PNG audit evidence.

See README section 8 and `outputs/study_v04/` for reproducibility. This is independent work; elite reinforcement is **not** attributed to the authors.
