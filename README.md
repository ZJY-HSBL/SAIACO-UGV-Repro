# SAIACO-UGV-Repro

## v0.2.0 — Reproduction audit and paired ablations / 复现审计与配对消融

**Research status / 研究状态:** The algorithm is implemented, but **strict numerical reproduction of the paper has not been achieved**. The figures do not disclose exact obstacle matrices, original endpoints or complete hyperparameters; claims are confined to independently digitized experimental maps. Six additional paper-figure maze *occupancy patterns* have been digitized, but their start and goal are **assumed experimental probes**.

**Reproducibility fixes:** A turning event is now defined by a change of heading, not by raw inequality of segment vectors. This prevents a collinear 2-cell segment followed by a 3-cell segment being counted as a turn. An exact Dijkstra reference for the corner-safe 8-connected graph is provided; its subsequently smoothed path is a **feasible comparison, not a certified continuous-path optimum**.

**Paired 3-seed exploratory study** (12 ants, 20 iterations, same seeds 0/1/2 per condition; lower length is better):

| 20×20 / 30×30 | Full SA-IACO | No SA | No direction | No smoothing |
|---|---:|---:|---:|---:|
| 20×20 mean length | 28.43 | 28.44 | 27.63 | 35.75 |
| 30×30 mean length | 48.41 | 49.37 | 48.39 | 58.08 |

![Ablation comparisons](outputs/study_v02/ablation.png)

All 6 special maps produced collision-free feasible paths in 3/3 seeds each, on the assumed start/goal probes. These numbers are **not** the original paper's results and the sample size is too small for claims of statistical significance. In both main maps, disabling smoothing caused a large deterioration; current tests did not establish positive added value from directional guidance or SA. The hybrid algorithm's raw search often failed to improve on its A* seed, so more optimization work is needed.

本轮已完成 18 项测试、Dijkstra 图最短路径参照、6 种特殊地图近似提取及 3 随机种子消融实验。**目前的主要性能收益来自路径平滑，尚不能证明模拟退火或方向引导带来稳定增益；不宣称完全数值复现。**

Run / 复现实验：

```bash
python scripts/study_v02.py --seeds 3 --ants 12 --iterations 20
```

Results: [summary.csv](outputs/study_v02/summary.csv), [per-seed runs.csv](outputs/study_v02/runs.csv), [deterministic references](outputs/study_v02/references.json), [map assumptions](docs/map_provenance.md). For a stronger statistical conclusion, increase independent seeds to at least 30 and test on held-out maps without tuning to these results.

---


**Simulated Annealing–Improved Ant Colony Optimization for Unmanned Ground Vehicle Path Planning**  
**基于模拟退火-改进蚁群算法的无人车路径规划——独立复现**

> **Status:** Tested independent implementation. **The paper's numerical results have NOT been exactly reproduced.**  
> **复现状态：** 已完成独立实现、自动化测试及初步基准实验，**尚未严格复现原论文的数值结果**。

## 1. Original paper / 原论文

- **Authors:** 朱梓轩、于莲芝 (Zhu Zixuan, Yu Lianzhi)
- **Journal:** 《电子科技》 / *Electronic Science and Technology*
- **Online first:** 2026-06-11
- **DOI:** https://doi.org/10.16180/j.cnki.issn1007-7820.2027.05.003
- **Reference environment:** MATLAB R2024b
- **This independent implementation:** Python 3.10+ with Matplotlib and pytest

This code is an independent reproduction, **not the authors' official implementation**. The article does not provide original grid matrices or all hyperparameters. See [map provenance and implementation assumptions](docs/map_provenance.md).

本仓库基于论文方法及公式独立实现，非作者官方代码。原文没有完整公开地图矩阵及实验超参数，因此对近似地图、参数假设、安全策略及复现误差单独说明。

## 2. Algorithms / 算法实现

Three experimental modes: **Classic ACO**, **Improved ACO**, and **SA-IACO**.

1. Four-neighbor A* initialization to generate a feasible seed path (section 2.1).
2. ACO pheromone–heuristic transition probability (Eq. 3).
3. Adaptive pheromone and heuristic exponents, alpha and beta (Eq. 9).
4. Direction-aware heuristic to reduce turning (Eqs. 10–12).
5. Weighted objective combining length, turns and curvature variation (Eqs. 13, 15–16).
6. Pheromone clipping and adaptive evaporation (Eqs. 17–18).
7. Simulated-annealing Metropolis acceptance and cooling (Eq. 19).
8. Dynamic-density interpolation and obstacle-safe waypoint removal (Eqs. 20–22).

实现经典蚁群、改进蚁群、模拟退火混合蚁群，包含简化 A* 初始化、动态信息素与启发因子、方向引导、多目标评分、信息素边界控制、Metropolis 准则及自适应密度路径平滑。

### Key equations / 核心公式

Transition probability / 状态转移概率：

$$
P_{ij}^{k}(t)=\frac{\tau_{ij}(t)^{\alpha}\eta_{ij}(t)^{\beta}}{\sum_{s\in allowed_k}\tau_{is}(t)^{\alpha}\eta_{is}(t)^{\beta}}
$$

Multiobjective score / 综合路径评分：

$$
S(k)=\xi L_k+\varphi N_k+\psi H_k
$$

Metropolis probability / 模拟退火接受概率：

$$
P=\exp\left(-\frac{E_{t+1}-E_t}{T}\right)
$$

**Implementation assumption:** ACO traverses eight neighbors without diagonal corner cutting; the seed A* traverses four neighbors. The smoother also uses conservative supercover collision checking. The paper does not fully specify these choices, so they affect numeric comparability.

## 3. Reproduced experiments / 实测结果

Default configuration: **30 ants × 60 iterations, seed 2026**. The `paper20` and `paper30` maps were independently digitized from printed plots, **not supplied as original MATLAB grids**.

### 20×20

![20x20 path comparison](outputs/paper20/paths.png)
![20x20 convergence](outputs/paper20/convergence.png)

| Algorithm | Our length | Our turns | Our smoothness | Paper length | Paper turns | Paper smoothness |
|:--|--:|--:|--:|--:|--:|--:|
| Classic ACO | 35.00 | 19 | 16.00 | 32.00 | 15 | 14.00 |
| Improved ACO | 35.00 | 8 | 13.00 | 32.00 | 9 | 13.41 |
| SA-IACO | **28.47** | **5** | **6.00** | **29.54** | **6** | **5.58** |

### 30×30

![30x30 path comparison](outputs/paper30/paths.png)
![30x30 convergence](outputs/paper30/convergence.png)

| Algorithm | Our length | Our turns | Our smoothness | Paper length | Paper turns | Paper smoothness |
|:--|--:|--:|--:|--:|--:|--:|
| Classic ACO | 74.00 | 44 | 32.00 | 51.40 | 25 | 22.65 |
| Improved ACO | 70.00 | 18 | 27.00 | 50.20 | 15 | 15.94 |
| SA-IACO | **48.39** | **11** | **5.30** | **44.70** | **6** | **0.94** |

Our numbers are **single-seed preliminary experiments**, not the authors' reported performance. In the 30×30 case, the hybrid's final improvement over the A* seed was mostly due to the collision-safe smoothing stage; raw score had not improved.

以上为本仓库真实运行的一次随机种子实验，不能视为原论文数值已完全复现。特别是 30×30 地图的传统与改进 ACO 基线仍与论文相差明显，需通过参数敏感性实验、多种子验证和地图人工复核继续研究。

## 4. Install / 安装和运行

```bash
git clone https://github.com/ZJY-HSBL/SAIACO-UGV-Repro.git
cd SAIACO-UGV-Repro
python -m pip install -e '.[test]'
pytest -q
saiaco-repro --map paper20 --ants 30 --iterations 60 --seed 2026
saiaco-repro --map paper30 --ants 30 --iterations 60 --seed 2026
```

Outputs: `outputs/<map>/paths.png`, `convergence.png`, `metrics.csv`, and `results.json`. GitHub Actions automatically regenerates benchmark artifacts after publishing.

Optional maze simulations: `saiaco-repro --map all --iterations 60 --ants 30 --seed 2026`. The extra U and X maps are illustrative rather than exact digitizations. `--goal-bias` is a clearly marked non-paper extension, default zero.

## 5. Repository layout / 项目结构

```text
src/saiaco_ugv/
  algorithms.py       # Classic ACO / improved ACO / SA-IACO
  grid.py             # Grid and A* / collision geometry
  metrics.py          # Length, turns and curvature variation
  smoothing.py        # Adaptive-density smoothing
  plotting.py         # Map and convergence figures
  cli.py              # Reproducible CLI
  maps/               # Figure-derived and illustrative maps
tests/                 # Automated tests
outputs/               # Experiment JSON, CSV and PNG generated in CI
docs/map_provenance.md # Source/parameter uncertainty
.github/workflows/    # Python CI and benchmark publication
```

## 6. Research roadmap / 后续研究

- 30+ independent random seeds; report confidence intervals and route-success rates.
- Ablations: direction heuristic, alpha/beta schedule, evaporation, SA, smoothing.
- Parameter sensitivity and manual verification of digitized obstacle maps.
- Collision clearance, obstacle-density sweeps and maze failure cases.
- Keep original paper metrics separate from independent empirical results.

**License:** MIT applies to independently written code only; copyright in the original paper and figures belongs to their respective owners.


## 7. v0.3.0: paired multi-seed RNG audit / 配对随机种子审计

**Study design:** 30 independent paired seeds 1000–1029 per configuration and map; 10 ants, 15 iterations, two figure-digitized maps (360 runs total). Full input and seed-level logs: [`outputs/study_v03/`](outputs/study_v03/). This is a new experimental configuration: **do not directly compare the means with v0.2.0**.

| Condition / 配置 | 20×20 mean length | 30×30 mean length |
|---|---:|---:|
| Full paper-inspired SA-IACO | **28.2672** | **48.6607** |
| No SA / 关闭退火 | 28.2672 | 48.6607 |
| No direction guidance / 无方向引导 | 27.5192 | 48.3951 |
| No smoothing / 无后处理平滑 | 35.2162 | 57.7752 |
| Elite SA reinforcement **(non-paper extension)** | 27.7354 | 48.5171 |
| Elite reinforcement without SA **(non-paper extension)** | 28.1377 | 48.6554 |

![Mean path length with bootstrap uncertainty](outputs/study_v03/mean_length_ci.png)

![Paired effect confidence intervals](outputs/study_v03/paired_effects.png)

![Search and smoothing length decomposition](outputs/study_v03/gain_decomposition.png)

**Most important finding:** once the ant and Metropolis random streams are separated, enabling/disabling the original SA decision produces **exactly identical paths in all 60 paired map–seed combinations**. The original implementation updates pheromone from all ant paths, while the SA-selected state is not fed back to ant transitions; therefore the observed v0.2.0 SA ablation differences were random-stream confounding, not evidence of SA improvement.

**Direction guidance:** without direction weighting, the average 20×20 path is 0.7480 shorter than the full variant (paired 95% bootstrap interval of “full minus no-direction”: −1.2699 to −0.3239 grid units, unadjusted sign-test p=0.00661). These are exploratory comparisons across multiple hypotheses; no family-wise multiplicity adjustment is claimed. The 30×30 effect remains uncertain.

**Smoothing:** average additional length reductions are 6.9490 and 9.1144 on 20×20 and 30×30 respectively. The fact that this dominates the pipeline **does not demonstrate SA search efficiency**.

**Non-paper extension:** `elite_deposit_weight=3.0` allows the accepted SA state to reinforce pheromone and affect subsequent ant trajectories. Compared with elite reinforcement without SA, the mean length reductions are +0.4023 (20×20; paired bootstrap CI [+0.0610,+0.7507]) and +0.1383 (30×30; CI [−0.0124,+0.3831]). The exact sign test is not significant (p=0.210 and 1.0 respectively). **These exploratory results do not establish a robust improvement**, and this variant is not attributed to the original authors.

**Reproduce / 重现实验：**
```bash
python scripts/study_v03.py --seeds 30 --seed-start 1000 --ants 10 --iterations 15 --bootstrap 4000
```

Raw data (`runs.csv`), summary (`summary.csv`), paired intervals (`paired_comparisons.csv`), configuration and map checksums (`manifest.json`) and plots are produced automatically and retained by CI. The reconstructed maps remain **unverified approximations** of the author's figures; these outcomes must not be presented as exact paper reproduction. Full interpretation: [v0.3.0 research note](docs/release-v0.3.0.md).


## 8. v0.4.0 held-out validation / 八图独立种子验证

**Independent confirmation, NOT another hyperparameter search.** 20 unseen paired seeds (2000–2019) × 8 approximately reconstructed paper-figure maps × 3 predeclared configurations = **480 genuine trials**. Parameters fixed at **10 ants, 15 iterations, elite reinforcement 3.0** (the reinforcement mechanism is an explicit *non-paper* extension). In six special mazes, start/goal positions remain assumed experimental probes.

**Method:** Each of the 20 random seeds first yields an equal-weight average of the paired *relative* effects over eight maps. Thus the independent statistical unit is the **seed**, not 160 correlated map/seed pairs. We report paired bootstrap 95% intervals and Holm-adjusted sign tests for **two predeclared primary hypotheses**. Per-map comparisons are exploratory and not multiplicity-adjusted.

| Primary comparison (lower path length is better) | Mean relative reduction | 95% paired bootstrap CI | Holm-adjusted p |
| --- | ---: | ---: | ---: |
| Elite SA vs elite greedy (effect of Metropolis acceptance) | **+0.06484%** | [−0.15149%, +0.29100%] | 0.53369 |
| Elite SA vs previous paper-inspired baseline (extension as a package) | **+0.47866%** | [−0.00254%, +0.95946%] | 0.53369 |

**Result:** Neither primary comparison passes a 0.05 family-wise threshold. SA does accept some higher-score candidates (diagnostics recorded), but that does **not** imply better final routes. Some special-map paths are identical for all seeds across all conditions, underscoring limited sensitivity of the final smoothing stage.

![Held-out primary comparisons](outputs/study_v04/heldout_primary.png)

![Exploratory per-map paired comparisons](outputs/study_v04/heldout_map_effects.png)

![Raw search vs smoothing](outputs/study_v04/search_vs_smoothing.png)

The original source paper reports a 30×30 path length of 44.70; this independent implementation still differs materially from that result. **Do not interpret extension results as reproduction of the published source paper.**

Evidence: [raw 480-run dataset](outputs/study_v04/runs.csv), [predeclared primary comparisons](outputs/study_v04/primary_comparisons.csv), [exploratory map comparisons](outputs/study_v04/exploratory_map_comparisons.csv), [per-map summary](outputs/study_v04/summary.csv), and [seed/map SHA-256 provenance](outputs/study_v04/manifest.json).

Re-run identically:

```bash
python scripts/study_v04.py --seed-start 2000 --seeds 20 --ants 10 --iterations 15 --bootstrap 4000
```

Next research priority: calibrate missing source maps and hyperparameters, diagnose pheromone entropy/route-diversity and distinguish ACO route selection from final smoothing. Preserve negative results; do not retune on this held-out confirmation cohort.
