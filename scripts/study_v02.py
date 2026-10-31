"""Paired multi-seed ablations and six special-map feasibility experiments.

All assumptions are explicit: maps digitized from printed figures; endpoints
are fixed evaluation probes. No hyperparameter tuning is performed here.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
from statistics import mean, stdev
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from saiaco_ugv import Grid, Config, AntColony, astar, evaluate, smooth_path, valid_path
from saiaco_ugv.oracles import shortest_grid_path, shortest_grid_path_smoothed
from saiaco_ugv.cli import MAPS

MAIN = ('paper20', 'paper30')
SPECIAL = ('u_maze', 'double_hook_maze', 'loop_maze',
           'traditional_maze', 'staircase_maze', 'x_maze')


def experiment(grid: Grid, map_name: str, seed: int, ants: int,
               iterations: int, condition: str) -> dict:
    options = {'ants': ants, 'iterations': iterations, 'seed': seed}
    if condition == 'no_sa':
        options['sa_enabled'] = False
    elif condition == 'no_direction':
        options['direction_u'] = 0
    elif condition == 'no_smoothing':
        options['smoothing_enabled'] = False
    elif condition != 'full':
        raise ValueError(condition)
    cfg = Config(**options)
    result = AntColony(grid, cfg, 'hybrid').run()
    if result.path and not valid_path(grid, result.path,
                                       allow_shortcuts=cfg.smoothing_enabled):
        raise AssertionError(f'Collision: {map_name} seed={seed} {condition}')
    metrics = evaluate(result.path) if result.path else None
    raw = evaluate(result.raw_path) if result.raw_path else None
    seed_metrics = evaluate(result.seed_path) if result.seed_path else None
    return dict(
        map=map_name, seed=seed, condition=condition, ants=ants,
        iterations=iterations,
        length=round(metrics.length, 6) if metrics else None,
        turns=metrics.turns if metrics else None,
        smoothness=round(metrics.smoothness, 6) if metrics else None,
        raw_length=round(raw.length, 6) if raw else None,
        astar_length=round(seed_metrics.length, 6) if seed_metrics else None,
        raw_search_gain=round(seed_metrics.length - raw.length, 6)
        if seed_metrics and raw else None,
        smoothing_gain=round(raw.length - metrics.length, 6)
        if raw and metrics else None,
        success_walks=result.successes,
        first_best_iteration=result.first_best_iteration)


def summarize(rows: list[dict]) -> list[dict]:
    out = []
    for name in sorted(set(row['map'] for row in rows)):
        for cond in sorted(set(row['condition'] for row in rows if row['map'] == name)):
            group = [row for row in rows if row['map'] == name and row['condition'] == cond]
            lengths = [row['length'] for row in group if row['length'] is not None]
            gains = [row['raw_search_gain'] for row in group if row['raw_search_gain'] is not None]
            out.append(dict(
                map=name, condition=cond, replicates=len(group),
                feasible=sum(row['length'] is not None for row in group),
                mean_length=round(mean(lengths), 4) if lengths else None,
                sd_length=round(stdev(lengths), 4) if len(lengths) > 1 else None,
                mean_raw_search_gain=round(mean(gains), 4) if gains else None))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=3)
    p.add_argument('--ants', type=int, default=12)
    p.add_argument('--iterations', type=int, default=20)
    p.add_argument('--out', type=Path, default=Path('outputs/study_v02'))
    args = p.parse_args()
    if min(args.seeds, args.ants, args.iterations) < 1:
        raise ValueError('Counts must be positive')
    args.out.mkdir(parents=True, exist_ok=True)
    maps = MAIN + SPECIAL
    grids = {name: Grid.from_text((MAPS / f'{name}.txt').read_text()) for name in maps}
    rows = []
    for name in MAIN:
        for seed in range(args.seeds):
            for condition in ('full', 'no_sa', 'no_direction', 'no_smoothing'):
                rows.append(experiment(grids[name], name, seed,
                                       args.ants, args.iterations, condition))
    for name in SPECIAL:
        for seed in range(args.seeds):
            rows.append(experiment(grids[name], name, seed,
                                   args.ants, args.iterations, 'full'))
    references = {}
    for name, grid in grids.items():
        four = astar(grid)
        eight = shortest_grid_path(grid)
        eight_smooth = shortest_grid_path_smoothed(grid)
        references[name] = {
            'astar4': round(evaluate(four).length, 6) if four else None,
            'dijkstra8': round(evaluate(eight).length, 6) if eight else None,
            'dijkstra8_shortcut_feasible': round(evaluate(eight_smooth).length, 6)
            if eight_smooth else None,
            'astar4_shortcut_feasible': round(evaluate(smooth_path(grid, four)).length, 6)
            if four else None,
            'start': grid.start, 'goal': grid.goal,
            'obstacles': sum(line.count('#') for line in grid.cells)}
    summary = summarize(rows)
    with (args.out / 'runs.csv').open('w', newline='', encoding='utf-8') as fp:
        wr = csv.DictWriter(fp, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)
    with (args.out / 'summary.csv').open('w', newline='', encoding='utf-8') as fp:
        wr = csv.DictWriter(fp, fieldnames=list(summary[0]))
        wr.writeheader()
        wr.writerows(summary)
    (args.out / 'references.json').write_text(
        json.dumps(references, indent=2, ensure_ascii=False) + '\n')
    (args.out / 'config.json').write_text(
        json.dumps(vars(args), indent=2, default=str) + '\n')
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), layout='constrained')
    conditions = ['full', 'no_sa', 'no_direction', 'no_smoothing']
    for ax, name in zip(axes, MAIN):
        ms = [next(s['mean_length'] for s in summary
                   if s['map'] == name and s['condition'] == c) for c in conditions]
        errors = [next(s['sd_length'] for s in summary
                       if s['map'] == name and s['condition'] == c) or 0 for c in conditions]
        ax.bar(conditions, ms, yerr=errors, capsize=4)
        ax.axhline(references[name]['dijkstra8_shortcut_feasible'],
                   linestyle='--', label='Dijkstra8 + shortcut (feasible)')
        ax.set_title(name)
        ax.set_ylabel('Final path length (grid units)')
        ax.tick_params(axis='x', labelrotation=25)
        ax.legend(fontsize=8)
    fig.savefig(args.out / 'ablation.png', dpi=160)
    plt.close(fig)
    print(json.dumps({'summary': summary, 'references': references},
                     indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
