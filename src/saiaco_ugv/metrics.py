"""Path scoring and metrics. Formula references: paper (13), (15), (16)."""
from __future__ import annotations
from dataclasses import dataclass
from math import hypot
from .grid import Point


@dataclass(frozen=True)
class Metrics:
    length: float
    turns: int
    smoothness: float

    def as_dict(self) -> dict[str, float | int]:
        return {'length': round(self.length, 6), 'turns': self.turns,
                'smoothness': round(self.smoothness, 6)}


def evaluate(path: list[Point]) -> Metrics:
    if len(path) < 2:
        return Metrics(0., 0, 0.)
    segments = [(b[1] - a[1], a[0] - b[0]) for a, b in zip(path, path[1:])]
    distance = sum(hypot(dx, dy) for dx, dy in segments)
    turns = sum(segments[i] != segments[i-1] for i in range(1, len(segments)))
    curvatures: list[float] = []
    for i in range(1, len(path)-1):
        ax, ay = segments[i-1]
        bx, by = segments[i]
        norm = hypot(bx, by)
        curvatures.append(abs(bx * ay - ax * by) / (norm ** 3) if norm else 0.0)
    smoothness = sum(abs(curvatures[i] - curvatures[i-1]) for i in range(1, len(curvatures)))
    return Metrics(distance, turns, smoothness)


def score(path: list[Point], weight_length: float = 1.0,
          weight_turns: float = 0.4, weight_smooth: float = 0.2) -> float:
    m = evaluate(path)
    return weight_length*m.length + weight_turns*m.turns + weight_smooth*m.smoothness
