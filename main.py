"""Data Extraction & Grid Mapping Tool

Extract an HTML table (x-coordinate | Character | y-coordinate) from Google Docs,
the web, or a file, rebuild it as a 2D grid, and print the resulting character art.

Usage:
    python main.py "https://docs.google.com/document/d/e/.../pub"
    python main.py samples/sample_F.html
    python main.py samples/sample_letters.html --origin top -o output/grid.txt
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from fetcher import load_html
from grid import build_grid, render, render_rows
from grid_parser import parse_html


def decode(source: str, origin: str = "bottom", fill: str = " ") -> str:
    """Build a grid from a URL or file path, print it, and return it as a string."""
    cells = parse_html(load_html(source))
    grid = build_grid(cells)
    result = render(grid, origin=origin, fill=fill)
    print(result)
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Data Extraction & Grid Mapping Tool")
    ap.add_argument("source", help="Google Docs/web URL or path to an .html/.txt file")
    ap.add_argument("--origin", choices=["bottom", "top"], default="bottom",
                    help="bottom: y increases upward (default) | top: y increases downward")
    ap.add_argument("--fill", default=" ", help="Character used for empty cells (default: space)")
    ap.add_argument("-o", "--output", help="Write the result to a .txt file (UTF-8)")
    ap.add_argument("-v", "--verbose", action="store_true", help="Enable detailed logging")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING,
                        format="%(levelname)-7s | %(name)s | %(message)s", stream=sys.stderr)
    # Print Unicode characters (█ ▀ ░) safely in the Windows terminal.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    try:
        grid = build_grid(parse_html(load_html(args.source)))
        if args.output:
            out = Path(args.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("w", encoding="utf-8") as f:  # Write each line as a stream.
                for line in render_rows(grid, origin=args.origin, fill=args.fill):
                    f.write(line + "\n")
            print(f"Saved {grid.width}x{grid.height} grid to {out}", file=sys.stderr)
        for line in render_rows(grid, origin=args.origin, fill=args.fill):
            print(line)
    except Exception as e:
        logging.getLogger("main").error("%s: %s", type(e).__name__, e)
        if args.verbose:
            raise
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
