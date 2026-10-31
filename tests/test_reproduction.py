from math import isclose
import pytest
from saiaco_ugv import Grid, astar, valid_path, evaluate, smooth_path, AntColony, Config
from saiaco_ugv.smoothing import checkpoints
from saiaco_ugv.cli import MAPS


def small():
    return Grid.from_text('S....\n.....\n..#..\n.....\n....G')


def test_grid_rejects_bad_inputs():
    with pytest.raises(ValueError): Grid.from_text('S..\n..G.\n')
    with pytest.raises(ValueError): Grid.from_text('S..\n...')


def test_astar_four_neighbor_shortest_empty():
    g = Grid.from_text('S...\n....\n....\n...G')
    path = astar(g)
    assert valid_path(g, path)
    assert isclose(evaluate(path).length, 6)


def test_diagonal_cannot_cross_blocked_corner():
    grid = Grid.from_text('S#\n.G')
    assert (1,1) not in grid.neighbors(grid.start)
    assert not grid.line_free(grid.start, grid.goal)
    assert astar(grid) == [(0,0), (1,0), (1,1)]


def test_smoothed_path_collision_free():
    grid = small()
    raw = astar(grid)
    smooth = smooth_path(grid, raw)
    assert valid_path(grid, smooth, allow_shortcuts=True)
    assert evaluate(smooth).length <= evaluate(raw).length + 1e-10


def test_score_metrics():
    p = [(2,0),(1,0),(1,1),(0,1)]
    m = evaluate(p)
    assert m.length == 3 and m.turns == 2 and m.smoothness >= 0


def test_checkpoints_density():
    assert len(checkpoints((0,0),(10,10),30)) > 50


def test_alpha_beta_paper_rule():
    g = small()
    for mode in ('improved','hybrid'):
        model = AntColony(g, Config(ants=2,iterations=2),mode)
        assert model.alpha_beta(1) == (4/7, 3-1.5/7)
        assert model.alpha_beta(7) == (3.5,1.0)


def test_modes_smoke_and_determinism():
    grid = Grid.from_text('S...\n....\n....\n...G')
    for mode in ('classic','improved','hybrid'):
        cfg = Config(ants=6,iterations=5,seed=1)
        result = AntColony(grid,cfg,mode).run()
        assert result.convergence == AntColony(grid,cfg,mode).run().convergence
        if result.path:
            assert valid_path(grid,result.path,allow_shortcuts=(mode=='hybrid'))


def test_figure_digitized_maps_are_connected():
    for name in ('paper20','paper30'):
        grid = Grid.from_text((MAPS / f'{name}.txt').read_text())
        assert grid.shape == ((20,20) if name=='paper20' else (30,30))
        assert astar(grid) is not None


def test_hybrid_improves_four_neighbor_seed_on_open_grid():
    g = Grid.from_text('S...\n....\n....\n...G')
    model = AntColony(g, Config(ants=20,iterations=30,seed=42),'hybrid')
    result = model.run()
    assert result.first_best_iteration is not None
    assert evaluate(result.raw_path).length < evaluate(result.seed_path).length
    assert valid_path(g,result.path,allow_shortcuts=True)

def test_turn_count_invariant_to_segment_length():
    assert evaluate([(0, 0), (0, 2), (0, 5)]).turns == 0
    assert evaluate([(0, 0), (0, 2), (0, 5), (2, 5)]).turns == 1
    assert evaluate([(0, 0), (0, 2), (0, 0)]).turns == 1


def test_dijkstra_oracle_exact_on_open_grid():
    from saiaco_ugv.oracles import shortest_grid_path, shortest_grid_path_smoothed
    from math import sqrt
    grid = Grid.from_text('S...\n....\n....\n...G')
    route = shortest_grid_path(grid)
    assert valid_path(grid, route)
    assert isclose(evaluate(route).length, 3 * sqrt(2))
    shortcut = shortest_grid_path_smoothed(grid)
    assert valid_path(grid, shortcut, allow_shortcuts=True)
    assert evaluate(shortcut).length <= evaluate(route).length + 1e-9


@pytest.mark.parametrize('name', ('u_maze','double_hook_maze','loop_maze',
                                   'traditional_maze','staircase_maze','x_maze'))
def test_six_special_paper_figures_have_feasible_graph_path(name):
    from saiaco_ugv.oracles import shortest_grid_path
    grid = Grid.from_text((MAPS / f'{name}.txt').read_text())
    assert grid.shape == (30, 30)
    assert shortest_grid_path(grid) is not None

def test_sa_rng_isolation_produces_identical_search_without_feedback():
    grid = Grid.from_text('S.......\n........\n...##...\n........\n.......G')
    active = AntColony(grid, Config(seed=71, iterations=12, ants=12, sa_enabled=True), 'hybrid').run()
    inactive = AntColony(grid, Config(seed=71, iterations=12, ants=12, sa_enabled=False), 'hybrid').run()
    assert active.convergence == inactive.convergence
    assert active.raw_path == inactive.raw_path
    assert active.path == inactive.path


def test_elite_pheromone_reinforcement_is_nonpaper_extension():
    grid = Grid.from_text('S....\n.....\n.....\n.....\n....G')
    assert Config().elite_deposit_weight == 0
    with pytest.raises(ValueError):
        Config(elite_deposit_weight=-0.1)
    result = AntColony(grid, Config(seed=3, ants=5, iterations=5, elite_deposit_weight=5), 'hybrid').run()
    assert valid_path(grid, result.path, allow_shortcuts=True)

def test_sa_instrumentation_and_greedy_negative_control():
    grid = Grid.from_text('S.....\n......\n......\n......\n.....G')
    config = Config(ants=6, iterations=10, seed=17, elite_deposit_weight=3)
    active = AntColony(grid, config, 'hybrid').run()
    greedy = AntColony(grid, Config(ants=6, iterations=10, seed=17,
                                    elite_deposit_weight=3, sa_enabled=False), 'hybrid').run()
    assert active.elite_deposit_rounds == greedy.elite_deposit_rounds == 10
    assert active.sa_uphill_accepted >= 0
    assert greedy.sa_uphill_accepted == 0
    assert active.sa_nonworse_accepted >= 0
    assert valid_path(grid, active.path, allow_shortcuts=True)
