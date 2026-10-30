"""CLI: saiaco-repro --map paper20 --iterations 40 --ants 20."""
from __future__ import annotations
import argparse, csv, json
from dataclasses import asdict
from pathlib import Path
from .grid import Grid, valid_path, astar
from .algorithms import AntColony, Config
from .metrics import evaluate
from .plotting import plot_routes, plot_convergence

MAPS = Path(__file__).resolve().with_name('maps')


def experiment(mapname: str, config: Config, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    grid = Grid.from_text((MAPS / f'{mapname}.txt').read_text(encoding='utf-8'))
    if not astar(grid):
        raise RuntimeError(f'{mapname} is disconnected for 4-neighbor A*')
    results = {mode: AntColony(grid, config, mode).run() for mode in ('classic', 'improved','hybrid')}
    rows = []
    serial = {}
    for mode, result in results.items():
        if result.path is not None and not valid_path(grid, result.path, allow_shortcuts=(mode=='hybrid')):
            raise AssertionError(f'INVALID PATH: {mapname}, {mode}')
        metrics = evaluate(result.path).as_dict() if result.path else None
        raw = evaluate(result.raw_path).as_dict() if result.raw_path else None
        row = {'map':mapname,'algorithm':mode, 'length':metrics['length'] if metrics else '',
               'turns':metrics['turns'] if metrics else '',
               'smoothness':metrics['smoothness'] if metrics else '',
               'first_best_iteration':result.first_best_iteration or '', 'successful_walks':result.successes}
        rows.append(row)
        serial[mode] = {'metrics':metrics, 'raw_metrics': raw, 'path':result.path,
                        'raw_path':result.raw_path, 'first_best_iteration':result.first_best_iteration,
                        'successful_walks':result.successes, 'convergence':result.convergence,
                        'seed_path': result.seed_path}
    report = {'map':mapname, 'shape':grid.shape,'config':asdict(config), 'algorithms': serial,
              'note': 'Figure-digitized map; unspecified paper parameters are assumed, not author verified.'}
    (output / 'results.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    with (output / 'metrics.csv').open('w', newline='', encoding='utf-8') as fp:
        writer = csv.DictWriter(fp, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    plot_routes(grid, results, str(output / 'paths.png'))
    plot_convergence(results, str(output / 'convergence.png'))
    return report


def main() -> None:
    p = argparse.ArgumentParser(description='SA-IACO reproduction: figure-digitized maps and three variants')
    p.add_argument('--map', choices=['paper20','paper30','u_maze','x_maze','all'], default='paper20')
    p.add_argument('--iterations', type=int, default=60)
    p.add_argument('--ants', type=int, default=30)
    p.add_argument('--seed', type=int, default=2026)
    p.add_argument('--goal-bias', type=float, default=0.0, help='Non-paper extension, default disabled')
    p.add_argument('--out', type=Path, default=Path('outputs'))
    args = p.parse_args()
    cfg = Config(ants=args.ants, iterations=args.iterations, seed=args.seed,
                 optional_goal_bias=args.goal_bias)
    maps = ['paper20','paper30','u_maze','x_maze'] if args.map == 'all' else [args.map]
    for name in maps:
        result = experiment(name, cfg, args.out / name)
        print(name, {k:v['metrics'] for k,v in result['algorithms'].items()})

if __name__ == '__main__':
    main()
