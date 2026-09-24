# Data Extraction & Grid Mapping Tool

A small Python tool for turning an HTML table into a character grid. It works with tables
from published Google Docs, web pages, or local files.

```
x-coordinate | Character | y-coordinate            █▀▀▀
     0       |     █     |      0          ==>     █▀▀
     0       |     █     |      1                  █
     1       |     ▀     |      1
     ...
```

## Project Structure

| File | Purpose |
|---|---|
| `fetcher.py` | Fetches HTML from a URL (converts Google Docs `/edit` links to `/export?format=html`) or reads a local file |
| `grid_parser.py` | Uses BeautifulSoup to find a table with x / Character / y columns in any order, clean the data, skip invalid rows, and fall back to plain-text parsing |
| `grid.py` | Builds a sparse grid and renders each row; supports negative coordinates, empty cells, and duplicate coordinates |
| `main.py` | CLI and `decode(url)` function |
| `tests/` | Pytest tests |
| `samples/` | Sample data |

## Installation (VS Code)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    |    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

In VS Code, press `Ctrl+Shift+P`, choose **Python: Select Interpreter**, and select `.venv`.

## Usage

```bash
python main.py samples/sample_F.html
python main.py "https://docs.google.com/document/d/e/XXXX/pub"
python main.py samples/sample_letters.html -o output/grid.txt     # write to a file
python main.py <source> --origin top      # when y increases downward (screen coordinates)
python main.py <source> --fill .          # show empty cells as dots
python main.py <source> -v                # enable detailed logging
```

To run the standalone local web server:

```bash
python server.py
```

Then open `http://127.0.0.1:8000` and submit the published Google Docs URL.

Alternatively, press **F5** in VS Code and select the *Grid Decoder: Enter URL* configuration.

Use it as a library:

```python
from main import decode
decode("https://docs.google.com/document/d/e/XXXX/pub")
```

## Vercel Deployment

The repository includes a Vercel serverless function at `/api/index.py`. Deploy the
repository to Vercel, then call it with a published document URL:

```text
https://your-project.vercel.app/api?source=https%3A%2F%2Fdocs.google.com%2Fdocument%2Fd%2Fe%2FXXXX%2Fpub
```

Optional query parameters are `origin=top` or `origin=bottom` and `fill=.`.

## Testing

```bash
pytest -q
```

## Technical Notes

- **Coordinate system:** by default, `y` increases upward (as in the original task), so rows are printed from the largest `y` value downward.
  If the output is upside down, use `--origin top`.
- **Memory:** the grid is stored sparsely as `{y: {x: character}}` and rendered row by row with a generator,
  so very tall or wide grids with little data use minimal memory. The DOM tree is decomposed immediately after parsing.
- **Google Docs:** the document must be *Published to the web* or shared with "Anyone with the link".
