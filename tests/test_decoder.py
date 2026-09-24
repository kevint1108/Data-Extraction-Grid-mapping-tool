import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from grid import build_grid, render  # noqa: E402
from grid_parser import Cell, parse_html, parse_text  # noqa: E402
from fetcher import normalize_url  # noqa: E402


def _table(header, rows):
    tr = lambda cells: "<tr>" + "".join(f"<td><p><span>{c}</span></p></td>" for c in cells) + "</tr>"
    return "<table>" + tr(header) + "".join(tr(r) for r in rows) + "</table>"


def test_sample_F_prints_upright():
    html = (ROOT / "samples" / "sample_F.html").read_bytes()
    assert render(build_grid(parse_html(html))) == "█▀▀▀\n█▀▀\n█"


def test_columns_in_any_order_and_gaps_filled():
    html = _table(["Character", "y-coordinate", "x-coordinate"], [["#", "0", "0"], ["#", "0", "3"]])
    assert render(build_grid(parse_html(html)), rstrip=False) == "#  #"


def test_origin_top():
    cells = [Cell(0, 0, "A"), Cell(0, 1, "B")]
    assert render(build_grid(cells), origin="top") == "A\nB"
    assert render(build_grid(cells), origin="bottom") == "B\nA"


def test_negative_coordinates_are_shifted():
    g = build_grid([Cell(-2, 0, "L"), Cell(2, 0, "R")])
    assert g.width == 5
    assert render(g) == "L   R"


def test_bad_rows_skipped_and_duplicates_overwrite():
    html = _table(["x-coordinate", "Character", "y-coordinate"],
                  [["0", "a", "0"], ["abc", "b", "0"], ["0", "c", "0"], ["1"]])
    assert render(build_grid(parse_html(html))) == "c"


def test_plain_text_fallback():
    assert render(build_grid(parse_text("0 █ 0\n1, ▀, 0\nrác\n"))) == "█▀"


def test_no_data_raises():
    with pytest.raises(ValueError):
        parse_html("<p>no data</p>")


def test_google_docs_url_normalization():
    assert normalize_url("https://docs.google.com/document/d/ABC_123/edit?usp=sharing") == \
        "https://docs.google.com/document/d/ABC_123/export?format=html"
    pub = "https://docs.google.com/document/d/e/2PACX-xyz/pub"
    assert normalize_url(pub) == pub


def test_large_sparse_grid_is_cheap():
    g = build_grid([Cell(0, 0, "a"), Cell(999, 999_999, "z")])
    assert g.height == 1_000_000 and g.count == 2  # Stores only two cells, not the full grid.
