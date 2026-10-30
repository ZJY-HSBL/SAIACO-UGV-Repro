# SAIACO-UGV-Repro

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
