"""Step 3 - Reconstruct a 2D grid from sparse coordinates.

Sparse storage: keep only cells that contain data and build each row while rendering.
This uses approximately O(number of cells + width) memory, independent of grid height.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Iterator

from grid_parser import Cell

log = logging.getLogger(__name__)


@dataclass
class Grid:
    rows: dict[int, dict[int, str]] = field(default_factory=lambda: defaultdict(dict))
    min_x: int = 0
    max_x: int = -1
    min_y: int = 0
    max_y: int = -1
    count: int = 0

    @property
    def width(self) -> int:
        return self.max_x - self.min_x + 1 if self.count else 0

    @property
    def height(self) -> int:
        return self.max_y - self.min_y + 1 if self.count else 0

    def get(self, x: int, y: int, default: str = " ") -> str:
        return self.rows.get(y, {}).get(x, default)


def build_grid(cells: Iterable[Cell]) -> Grid:
    g = Grid()
    first = True
    for c in cells:
        row = g.rows[c.y]
        if c.x in row and row[c.x] != c.char:
            log.warning("Duplicate coordinate (%d, %d): '%s' overwrites '%s'",
                        c.x, c.y, c.char, row[c.x])
        elif c.x not in row:
            g.count += 1
        row[c.x] = c.char
        if first:
            g.min_x = g.max_x = c.x
            g.min_y = g.max_y = c.y
            first = False
        else:
            g.min_x, g.max_x = min(g.min_x, c.x), max(g.max_x, c.x)
            g.min_y, g.max_y = min(g.min_y, c.y), max(g.max_y, c.y)
    log.info("Grid %d x %d (width x height), %d populated cells",
             g.width, g.height, g.count)
    return g


def render_rows(g: Grid, origin: str = "bottom", fill: str = " ",
                rstrip: bool = True) -> Iterator[str]:
    """Generate the grid's text rows.

    origin="bottom": y increases upward (Cartesian coordinates, as in the original
                     Google Docs task), so rows are printed from largest y to smallest.
    origin="top":    y increases downward (screen coordinates).
    """
    if not g.count:
        return
    ys = range(g.max_y, g.min_y - 1, -1) if origin == "bottom" else range(g.min_y, g.max_y + 1)
    for y in ys:
        line = [fill] * g.width  # Rebuild the row buffer to avoid memory accumulation.
        for x, ch in g.rows.get(y, {}).items():
            line[x - g.min_x] = ch
        text = "".join(line)
        yield text.rstrip() if rstrip else text


def render(g: Grid, **kw) -> str:
    return "\n".join(render_rows(g, **kw))
