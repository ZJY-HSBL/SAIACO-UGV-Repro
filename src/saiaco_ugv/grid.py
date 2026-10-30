"""Grid and collision geometry for the reproduced UGV path-planning experiments."""
from __future__ import annotations
from dataclasses import dataclass
from heapq import heappop, heappush
from math import hypot
from typing import Iterable

Point = tuple[int, int]


@dataclass(frozen=True)
class Grid:
    cells: tuple[str, ...]
    start: Point
    goal: Point

    @classmethod
    def from_text(cls, text: str) -> "Grid":
        rows = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith(';')]
        if not rows or len(set(map(len, rows))) != 1:
            raise ValueError('Expected a nonempty rectangular map')
        if any(char not in '.#SG' for line in rows for char in line):
            raise ValueError('Allowed map symbols are . # S G')
        starts = [(r, c) for r, line in enumerate(rows) for c, ch in enumerate(line) if ch == 'S']
        goals = [(r, c) for r, line in enumerate(rows) for c, ch in enumerate(line) if ch == 'G']
        if len(starts) != 1 or len(goals) != 1:
            raise ValueError('Map requires exactly one S and one G')
        return cls(tuple(rows), starts[0], goals[0])

    @property
    def shape(self) -> tuple[int, int]:
        return len(self.cells), len(self.cells[0])

    def free(self, pt: Point) -> bool:
        r, c = pt
        return 0 <= r < len(self.cells) and 0 <= c < len(self.cells[0]) and self.cells[r][c] != '#'

    def neighbors(self, pt: Point, diagonal: bool = True, prevent_corner_cut: bool = True) -> list[Point]:
        r, c = pt
        directions = [(0, 1), (1, 0), (-1, 0), (0, -1)]
        if diagonal:
            directions += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        out = []
        for dr, dc in directions:
            target = (r + dr, c + dc)
            if not self.free(target):
                continue
            if prevent_corner_cut and dr and dc and (not self.free((r + dr, c)) or not self.free((r, c + dc))):
                continue
            out.append(target)
        return out

    def line_free(self, start: Point, end: Point) -> bool:
        if not self.free(start) or not self.free(end):
            return False
        r, c = start
        r_end, c_end = end
        dr, dc = r_end - r, c_end - c
        if not dr and not dc:
            return True
        sr = 1 if dr > 0 else -1
        sc = 1 if dc > 0 else -1
        ar, ac = abs(dr), abs(dc)
        steps_r = steps_c = 0
        while (r, c) != end:
            tr = (steps_r + 0.5) / ar if ar else float('inf')
            tc = (steps_c + 0.5) / ac if ac else float('inf')
            if abs(tr - tc) < 1e-12:
                if not self.free((r + sr, c)) or not self.free((r, c + sc)):
                    return False
                r += sr
                c += sc
                steps_r += 1
                steps_c += 1
            elif tr < tc:
                r += sr
                steps_r += 1
            else:
                c += sc
                steps_c += 1
            if not self.free((r, c)):
                return False
        return True


def astar(grid: Grid, diagonal: bool = False) -> list[Point] | None:
    start, goal = grid.start, grid.goal
    pq: list[tuple[float, int, Point]] = [(0., 0, start)]
    counter = 1
    g = {start: 0.0}
    parents: dict[Point, Point] = {}
    while pq:
        f, _, current = heappop(pq)
        if f > g[current] + hypot(goal[0] - current[0], goal[1] - current[1]) + 1e-9:
            continue
        if current == goal:
            route = [goal]
            while route[-1] != start:
                route.append(parents[route[-1]])
            return route[::-1]
        for nxt in grid.neighbors(current, diagonal=diagonal):
            cand = g[current] + hypot(nxt[0] - current[0], nxt[1] - current[1])
            if cand + 1e-12 < g.get(nxt, float('inf')):
                g[nxt] = cand
                parents[nxt] = current
                heappush(pq, (cand + hypot(goal[0] - nxt[0], goal[1] - nxt[1]), counter, nxt))
                counter += 1
    return None


def valid_path(grid: Grid, path: Iterable[Point], allow_shortcuts: bool = False) -> bool:
    pts = list(path)
    if not pts or pts[0] != grid.start or pts[-1] != grid.goal:
        return False
    for a, b in zip(pts, pts[1:]):
        if allow_shortcuts:
            if not grid.line_free(a, b):
                return False
        else:
            if b not in grid.neighbors(a, diagonal=True):
                return False
    return True
