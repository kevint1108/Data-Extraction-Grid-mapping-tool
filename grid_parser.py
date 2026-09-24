"""Step 2 - Parse and clean (x, character, y) data from HTML or plain text."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Iterable, Iterator

from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Cell:
    x: int
    y: int
    char: str


# Accepted column names, matched after lowercasing and collapsing whitespace.
HEADER_ALIASES: dict[str, tuple[str, ...]] = {
    "x": ("x-coordinate", "x coordinate", "x_coordinate", "x", "col", "column", "toạ độ x", "tọa độ x"),
    "y": ("y-coordinate", "y coordinate", "y_coordinate", "y", "row", "toạ độ y", "tọa độ y"),
    "char": ("character", "char", "symbol", "glyph", "ký tự", "kí tự"),
}

_WS = re.compile(r"\s+")
_INT = re.compile(r"^[+-]?\d+(?:\.0+)?$")


def _norm(text: str) -> str:
    return _WS.sub(" ", text.replace("\xa0", " ")).strip().lower()


def _cell_text(tag) -> str:
    # Google Docs wraps content in <p><span>...; get_text() combines it all.
    return tag.get_text("", strip=False).replace("\xa0", " ")


def _match_header(row: list[str]) -> dict[str, int] | None:
    """Find the x, y, and character columns in a row, in any order."""
    mapping: dict[str, int] = {}
    for idx, raw in enumerate(row):
        name = _norm(raw)
        for key, aliases in HEADER_ALIASES.items():
            if key not in mapping and name in aliases:
                mapping[key] = idx
                break
    return mapping if len(mapping) == 3 else None


def _to_int(text: str) -> int | None:
    t = _norm(text)
    return int(float(t)) if _INT.match(t) else None


def _rows_to_cells(rows: Iterable[list[str]], cols: dict[str, int]) -> Iterator[Cell]:
    need = max(cols.values())
    for n, row in enumerate(rows, start=1):
        if len(row) <= need:
            log.debug("Skipping row %d: missing columns (%r)", n, row)
            continue
        x, y = _to_int(row[cols["x"]]), _to_int(row[cols["y"]])
        if x is None or y is None:
            log.warning("Skipping row %d: invalid coordinates (%r)", n, row)
            continue
        ch = row[cols["char"]].strip("\r\n\t")
        ch = ch.strip() or " "  # Empty cells become spaces.
        if len(ch) > 1:
            log.warning("Row %d: character cell contains %d characters (%r); using the first",
                        n, len(ch), ch)
            ch = ch[0]
        yield Cell(x, y, ch)


def parse_html(html: bytes | str) -> list[Cell]:
    """Scan every <table> and use the first one with x, character, and y columns."""
    soup = BeautifulSoup(html, "html.parser")
    for t_idx, table in enumerate(soup.find_all("table")):
        rows = [[_cell_text(td) for td in tr.find_all(["td", "th"])] for tr in table.find_all("tr")]
        for h_idx, row in enumerate(rows):
            cols = _match_header(row)
            if cols:
                log.info("Using table #%d, header row %d, columns=%s", t_idx, h_idx, cols)
                cells = list(_rows_to_cells(rows[h_idx + 1:], cols))
                soup.decompose()  # Release the DOM tree as soon as parsing is complete.
                return cells

    # No suitable table found; try parsing plain text instead.
    text = soup.get_text("\n")
    soup.decompose()
    log.info("No table with x/character/y headers found; parsing plain text instead")
    return parse_text(text)


# Dòng dạng: "0 █ 1", "0, █, 1", "0\t█\t1"
_TRIPLE = re.compile(r"^\s*([+-]?\d+)\s*[,;\t ]\s*(\S)\s*[,;\t ]\s*([+-]?\d+)\s*$")


def parse_text(text: str) -> list[Cell]:
    """Parse plain text as a fallback, with one x <character> y entry per line."""
    cells = [Cell(int(m[1]), int(m[3]), m[2]) for line in text.splitlines() if (m := _TRIPLE.match(line))]
    if not cells:
        raise ValueError(
            "No coordinate data found. Expected a table with 'x-coordinate', 'Character', "
            "'y-coordinate' columns or plain-text lines in the form 'x character y'."
        )
    return cells
