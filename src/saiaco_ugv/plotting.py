"""Publication-ready figure rendering with headless Matplotlib."""
from __future__ import annotations
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from .grid import Grid
from .algorithms import Result


def plot_routes(grid: Grid, results: dict[str, Result], outfile: str) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), constrained_layout=True)
    names = [('classic', 'Classic ACO'), ('improved', 'Improved ACO'), ('hybrid', 'SA-IACO + smoothing')]
    image = [[1 if ch == '#' else 0 for ch in row] for row in grid.cells]
    for ax, (mode, title) in zip(axes, names):
        ax.imshow(image, cmap=ListedColormap(['#f7f9fc', '#27333e']), interpolation='none', origin='upper')
        nrows, ncols = grid.shape
        ax.set_xticks([i-.5 for i in range(ncols+1)], minor=True)
        ax.set_yticks([i-.5 for i in range(nrows+1)], minor=True)
        ax.grid(which='minor', color='#a9b4c0', alpha=.35, linewidth=.4)
        ax.tick_params(which='minor', bottom=False, left=False)
        ax.scatter([grid.start[1]], [grid.start[0]], s=55, marker='o', label='Start', zorder=4)
        ax.scatter([grid.goal[1]], [grid.goal[0]], s=65, marker='*', label='Goal', zorder=4)
        res = results.get(mode)
        if res and res.path:
            ax.plot([p[1] for p in res.path], [p[0] for p in res.path], linewidth=2, label='Path')
        else:
            ax.text(.5, .5, 'No feasible route', transform=ax.transAxes, ha='center',
                    va='center', bbox={'facecolor': 'white', 'alpha': .85})
        ax.set_title(title)
        ax.set_xlim(-.5,ncols-.5)
        ax.set_ylim(nrows-.5,-.5)
        ax.set_xlabel('column')
        ax.set_ylabel('row')
    fig.savefig(outfile, dpi=175)
    plt.close(fig)


def plot_convergence(results: dict[str, Result], outfile: str) -> None:
    fig, ax = plt.subplots(figsize=(9, 5), layout='constrained')
    for mode, label in [('classic', 'Classic ACO'),('improved', 'Improved ACO'),('hybrid', 'SA-IACO (unsmoothed)')]:
        if mode in results:
            ys = [float('nan') if val is None else val for val in results[mode].convergence]
            ax.plot(range(1, len(ys)+1), ys, label=label)
    ax.set_xlabel('Iteration')
    ax.set_ylabel('Best raw path length (grid units)')
    ax.set_title('Convergence – last-step smoothing excluded')
    ax.grid(alpha=.25)
    ax.legend()
    fig.savefig(outfile, dpi=175)
    plt.close(fig)
