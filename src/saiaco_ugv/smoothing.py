"""Distance-adaptive waypoint interpolation and obstacle-safe path shortcutting."""
from __future__ import annotations
from math import ceil, hypot
from .grid import Grid, Point


def checkpoints(a: Point, b: Point, grid_size: int) -> list[Point]:
    dist = hypot(a[0]-b[0], a[1]-b[1])
    density = 5 if dist <= grid_size * 2**0.5 / 6 else 10
    count = max(2, ceil(density * max(abs(a[0]-b[0]), abs(a[1]-b[1]))) + 1)
    return [(round(a[0] + (b[0]-a[0])*i/(count-1)),
             round(a[1] + (b[1]-a[1])*i/(count-1))) for i in range(count)]


def smooth_path(grid: Grid, original: list[Point]) -> list[Point]:
    path = list(original)
    if len(path) < 3:
        return path
    size = max(grid.shape)
    changed = True
    while changed:
        changed = False
        i = 1
        while i < len(path)-1:
            a, b = path[i-1], path[i+1]
            if all(grid.free(p) for p in checkpoints(a, b, size)) and grid.line_free(a, b):
                path.pop(i)
                changed = True
            else:
                i += 1
    return path
