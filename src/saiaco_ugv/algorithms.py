"""Classical ACO, dynamically improved ACO, and paper-inspired SA-IACO."""
from __future__ import annotations
from dataclasses import dataclass
from math import exp, hypot
import random
from .grid import Grid, Point, astar
from .metrics import evaluate, score
from .smoothing import smooth_path

Edge = tuple[Point, Point]


def edge(a: Point, b: Point) -> Edge:
    return tuple(sorted((a, b)))  # type: ignore[return-value]


@dataclass
class Config:
    ants: int = 30
    iterations: int = 60
    seed: int = 2026
    alpha: float = 1.0
    beta: float = 3.0
    q: float = 20.0
    rho: float = 0.35
    rho_min: float = 0.10
    rho_max: float = 0.75
    tau_min: float = 0.05
    tau_max: float = 18.0
    direction_u: float = 2.0
    c: float = 7.0  # The paper does not define c in Eq (9).
    weight_length: float = 1.0
    weight_turns: float = 0.4
    weight_smooth: float = 0.2
    init_temp: float = 8.0
    cooling: float = 0.95
    seed_pheromone: float = 6.0
    optional_goal_bias: float = 0.0
    step_limit: int = 0
    recover_deadends: bool = True
    sa_enabled: bool = True  # Greedy-acceptance ablation switch
    smoothing_enabled: bool = True  # Disable final smoothing for ablation
    elite_deposit_weight: float = 0.0  # Non-paper SA-selected elite pheromone extension

    def __post_init__(self) -> None:
        if self.ants < 1 or self.iterations < 1 or self.c <= 0 or self.init_temp <= 0 or self.elite_deposit_weight < 0:
            raise ValueError('Ants, iterations, c and initial temperature must be positive')
        if not 0 < self.cooling <= 1:
            raise ValueError('Cooling must be in (0,1]')
        if not 0 < self.rho_min < self.rho_max < 1:
            raise ValueError('Require 0 < rho_min < rho_max < 1')


@dataclass
class Result:
    algorithm: str
    path: list[Point] | None
    raw_path: list[Point] | None
    convergence: list[float | None]
    first_best_iteration: int | None
    successes: int
    seed_path: list[Point] | None = None


class AntColony:
    def __init__(self, grid: Grid, config: Config, mode: str):
        if mode not in {'classic', 'improved', 'hybrid'}:
            raise ValueError('mode must be classic, improved or hybrid')
        self.grid, self.config, self.mode = grid, config, mode
        # Separate ant trajectory and Metropolis streams for paired experiments.
        self.rng = random.Random(config.seed)
        self.sa_rng = random.Random(config.seed ^ 0x5A17DE5A)
        self.pheromone: dict[Edge, float] = {}
        self.seed_path = astar(grid, diagonal=False) if mode == 'hybrid' else None
        if self.seed_path is not None:
            for a, b in zip(self.seed_path, self.seed_path[1:]):
                self.pheromone[edge(a, b)] = config.seed_pheromone

    def alpha_beta(self, iteration: int) -> tuple[float, float]:
        cfg = self.config
        if self.mode == 'classic':
            return cfg.alpha, cfg.beta
        if iteration < 7:
            return 4*iteration/cfg.c, (3*cfg.c - 1.5*iteration)/cfg.c
        return 3.5, 1.0

    def heuristic(self, current: Point, nxt: Point, previous: Point | None,
                  available_count: int) -> float:
        cfg = self.config
        value = 1 / hypot(nxt[0]-current[0], nxt[1]-current[1])
        if self.mode != 'classic':
            if previous is None:
                value += cfg.direction_u / available_count
            elif (current[0]-previous[0], current[1]-previous[1]) == (nxt[0]-current[0], nxt[1]-current[1]):
                value += 0.7*cfg.direction_u
            else:
                value += 0.3*cfg.direction_u/available_count
        if cfg.optional_goal_bias:
            value *= (1 + cfg.optional_goal_bias /
                      (1 + hypot(nxt[0]-self.grid.goal[0], nxt[1]-self.grid.goal[1])))
        return value

    def walk(self, alpha: float, beta: float) -> list[Point] | None:
        cfg = self.config
        path = [self.grid.start]
        visited = {self.grid.start}
        maximum = cfg.step_limit or self.grid.shape[0]*self.grid.shape[1]
        for _ in range(maximum):
            current = path[-1]
            if current == self.grid.goal:
                return path
            available = [n for n in self.grid.neighbors(current) if n not in visited]
            if not available:
                if not cfg.recover_deadends or len(path) <= 1:
                    return None
                path.pop()
                continue
            prev = path[-2] if len(path) > 1 else None
            weights = [max(1e-10, self.pheromone.get(edge(current, nxt), 1.)) ** alpha *
                       max(1e-10, self.heuristic(current, nxt, prev, len(available))) ** beta
                       for nxt in available]
            next_node = self.rng.choices(available, weights=weights, k=1)[0]
            path.append(next_node)
            visited.add(next_node)
        return path if path[-1] == self.grid.goal else None

    def path_score(self, path: list[Point]) -> float:
        if self.mode == 'classic':
            return evaluate(path).length
        cfg = self.config
        return score(path, cfg.weight_length, cfg.weight_turns, cfg.weight_smooth)

    def run(self) -> Result:
        cfg = self.config
        global_best = None
        global_score = float('inf')
        sa_state = self.seed_path
        sa_state_score = self.path_score(self.seed_path) if self.seed_path else float('inf')
        if self.seed_path is not None:
            global_best = self.seed_path
            global_score = sa_state_score
        initial_length = evaluate(self.seed_path).length if self.seed_path else None
        best_iter = None
        convergence: list[float | None] = []
        successes = 0
        temperature = cfg.init_temp
        for it in range(1, cfg.iterations + 1):
            alpha, beta = self.alpha_beta(it)
            solutions = []
            for _ in range(cfg.ants):
                p = self.walk(alpha, beta)
                if p is not None:
                    solutions.append(p)
                    successes += 1
            solutions.sort(key=self.path_score)
            candidate = solutions[0] if solutions else None
            if candidate is not None:
                cand_score = self.path_score(candidate)
                if self.mode == 'hybrid':
                    delta = cand_score - sa_state_score
                    if delta < 0 or (cfg.sa_enabled and self.sa_rng.random() < exp(-max(0, delta) / max(temperature, 1e-12))):
                        sa_state, sa_state_score = candidate, cand_score
                    considered = sa_state
                else:
                    considered = candidate
                considered_score = self.path_score(considered)
                if considered_score < global_score - 1e-10:
                    global_score, global_best, best_iter = considered_score, list(considered), it
            convergence.append(round(evaluate(global_best).length, 5) if global_best else None)
            if self.mode == 'classic':
                rho = cfg.rho
            else:
                if initial_length is None and global_best:
                    initial_length = evaluate(global_best).length
                best_len = evaluate(global_best).length if global_best else initial_length
                rho = min(cfg.rho_max, max(cfg.rho_min,
                            cfg.rho*(initial_length/best_len) if initial_length and best_len else cfg.rho))
            for e in list(self.pheromone):
                updated = (1-rho)*self.pheromone[e]
                self.pheromone[e] = max(cfg.tau_min, min(cfg.tau_max, updated)) if self.mode != 'classic' else updated
            for p in solutions:
                inc = cfg.q / max(evaluate(p).length, 1e-10)
                for a, b in zip(p, p[1:]):
                    e = edge(a, b)
                    value = self.pheromone.get(e, (1-rho)) + inc
                    self.pheromone[e] = max(cfg.tau_min, min(cfg.tau_max, value)) if self.mode != 'classic' else value
            # Explicit non-paper extension: the SA-selected state influences
            # future trajectories only when elite_deposit_weight is nonzero.
            if self.mode == 'hybrid' and cfg.elite_deposit_weight and sa_state:
                elite_gain = cfg.elite_deposit_weight * cfg.q / max(evaluate(sa_state).length, 1e-10)
                for a, b in zip(sa_state, sa_state[1:]):
                    e = edge(a, b)
                    value = self.pheromone.get(e, 1.0 - rho) + elite_gain
                    self.pheromone[e] = max(cfg.tau_min, min(cfg.tau_max, value))
            temperature *= cfg.cooling
        raw = list(global_best) if global_best else None
        final = smooth_path(self.grid, raw) if raw and self.mode == 'hybrid' and cfg.smoothing_enabled else raw
        return Result(self.mode, final, raw, convergence, best_iter, successes, self.seed_path)
