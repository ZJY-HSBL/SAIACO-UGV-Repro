# Map provenance and reproduction limits

Original paper: Zhu Zixuan and Yu Lianzhi (2026), DOI 10.16180/j.cnki.issn1007-7820.2027.05.003.

The authors did **not** publish raw obstacle matrices. `paper20.txt` and `paper30.txt` were digitized from PDF illustrations, not imported from their simulation environment. Figures 3–5 (PDF page 6) provided 20×20; Figures 7–9 (PDF page 7) provided 30×30. The original edition was rendered at 125 DPI; the central part of each cell was dark-pixel thresholded and combined across three figures by a median vote.

- `paper20.txt`: start row 3, col 0; goal row 19, col 19.
- `paper30.txt`: start row 29, col 0; goal row 0, col 29.
- `u_maze.txt` and `x_maze.txt`: illustrative maps only; **not** the exact published special environments.

**Unknown author parameters:** colony population, random seed, Q, direction-guidance coefficient u, constant c in Eq. 9, pheromone bounds, scoring weights, cooling constant and schedule, MATLAB random state and corner-cutting policy. Our constants in `Config` are independent research assumptions, not confirmed original parameters.

Eq. 18 contains an incompletely defined length reference; we use initial feasible route length. We also use backtracking for dead ends and add a conservative supercover collision test in the smoother. Those safety decisions can lead to longer paths than the article.

Original performance tables are for reference only. This repository must not claim its results exactly match the original until parameters/maps and independent statistics are confirmed.


## v0.2 addendum — special-figure reconstruction

Figures 11–14 from original PDF page 8 and Figures 15–16 from page 9 were rendered at 2.5× and approximately segmented by central-cell dark-pixel thresholding. Reconstruction crop boxes and thresholds are preserved in `scripts/extract_special_maps.py` (needs PyMuPDF, NumPy, Pillow if rerun). The six reconstructed environments resemble the paper diagrams but are **not verified exact source grids**; plotted solution polylines can obscure some obstacle cells and produce extraction artifacts.

Each special scenario in v0.2 fixes test start=(29,0) and goal=(0,29) in Python (row,column). These are **chosen test probes**; source figures do not unambiguously identify the authors' start/goal. The full method is evaluated for reachability and obstacle collision safety, not claimed to match their route length or waypoints.

## v0.2 metric correction and deterministic reference

Previous implementation compared successive raw segment vectors for equality. Such vectors have unequal magnitudes after smoothing, so straight collinear segments could be falsely counted as turns. We now use cross product = 0 and positive dot product to detect a consistent heading. The Dijkstra 8-neighbor oracle is exact within the same grid graph and diagonal corner-cut constraints as the code, but it does not certify globally shortest paths once arbitrary straight-line shortcuts are allowed.

A three-seed ablation study is exploratory, not a statistical demonstration. No benchmark parameters are fit to the published table. SA and directional guidance benefits remain uncertain.
