from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from fetcher import load_html
from grid import build_grid, render
from grid_parser import parse_html


class GridRequestHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: str, content_type: str = "text/plain") -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        source = query.get("source", [""])[0]
        if not source:
            self._send(200, """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>Grid Decoder</title>
<h1>Grid Decoder</h1>
<form action="/api" method="get">
  <label>Published Google Docs URL
    <input name="source" type="url" required size="80">
  </label>
  <button type="submit">Decode</button>
</form>
""", "text/html")
            return

        if not source.startswith(("http://", "https://")):
            self._send(400, "source must be an HTTP or HTTPS URL\n")
            return

        origin = query.get("origin", ["bottom"])[0]
        fill = query.get("fill", [" "])[0]
        if origin not in {"bottom", "top"}:
            self._send(400, "origin must be 'bottom' or 'top'\n")
            return

        try:
            cells = parse_html(load_html(source))
            result = render(build_grid(cells), origin=origin, fill=fill)
        except Exception as error:
            self._send(422, json.dumps({"error": str(error)}) + "\n", "application/json")
            return

        self._send(200, result + "\n")


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), GridRequestHandler)
    print("Grid Decoder running at http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Grid Decoder")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()