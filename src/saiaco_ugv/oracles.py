"""Deterministic shortest-path references independent of ACO randomness.

The 8-neighbor Dijkstra route is exact only in the corner-safe adjacency graph.
Smoothing it yields a feasible comparison, NOT a continuous-space optimum.
"""
from __future__ import annotations
from heapq import heappop, heappush
from math import hypot
from .grid import Grid, Point
from .smoothing import smooth_path


def shortest_grid_path(grid: Grid, diagonal: bool = True) -> list[Point] | None:
    dist = {grid.start: 0.0}
    previous: dict[Point, Point] = {}
    queue = [(0.0, grid.start)]
    while queue:
        cost, node = heappop(queue)
        if cost > dist[node] + 1e-12:
            continue
        if node == grid.goal:
            out = [node]
            while out[-1] != grid.start:
                out.append(previous[out[-1]])
            return out[::-1]
        for nxt in grid.neighbors(node, diagonal=diagonal):
            step = hypot(nxt[0]-node[0], nxt[1]-node[1])
            new = cost + step
            if new < dist.get(nxt, float('inf')) - 1e-12:
                dist[nxt] = new
                previous[nxt] = node
                heappush(queue, (new, nxt))
    return None


def shortest_grid_path_smoothed(grid: Grid) -> list[Point] | None:
    """Feasible shortcut of graph optimum, not a proven continuous optimum."""
    route = shortest_grid_path(grid, diagonal=True)
    return smooth_path(grid, route) if route else None
