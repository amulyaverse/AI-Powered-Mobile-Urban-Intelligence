"""
GPS simulator for the hackathon demo.

There's no real bus/GPS hardware, so this fakes a route by cycling
through coordinates from a CSV file. Falls back to one hardcoded
point in Delhi if no CSV is found.

CSV format (no header row): latitude,longitude
"""

import csv
import itertools
from pathlib import Path
from typing import Iterator, List, Tuple

DEFAULT_ROUTE_CSV = Path(__file__).parent / "sample_route.csv"

# Fallback point if no CSV is present
FALLBACK_POINT = (28.6139, 77.2090)


def load_route(csv_path: Path = DEFAULT_ROUTE_CSV) -> List[Tuple[float, float]]:
    if not csv_path.exists():
        return [FALLBACK_POINT]
    points = []
    with open(csv_path, newline="") as f:
        for row in csv.reader(f):
            if not row:
                continue
            lat, lon = float(row[0]), float(row[1])
            points.append((lat, lon))
    return points or [FALLBACK_POINT]


class GPSSimulator:
    """Call .next() once per frame/detection to get the 'current' GPS fix."""

    def __init__(self, csv_path: Path = DEFAULT_ROUTE_CSV):
        self._points = load_route(csv_path)
        self._cycle: Iterator[Tuple[float, float]] = itertools.cycle(self._points)

    def next(self) -> Tuple[float, float]:
        return next(self._cycle)


if __name__ == "__main__":
    sim = GPSSimulator()
    for _ in range(5):
        print(sim.next())
