from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

import requests

from fetcher import load_html
from grid import render
from grid_parser import parse_html


def _response(handler: BaseHTTPRequestHandler, status: int, body: str) -> None:
    payload = body.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/plain; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(payload)


def _form_response(handler: BaseHTTPRequestHandler) -> None:
        body = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Grid Decoder</title></head>
<body>
    <h1>Grid Decoder</h1>
    <form action="/api" method="get">
        <label for="source">Published Google Docs URL</label>
        <input id="source" name="source" type="url" required
                     placeholder="https://docs.google.com/document/d/e/.../pub">
        <button type="submit">Decode</button>
    </form>
</body>
</html>
"""
        payload = body.encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "text/html; charset=utf-8")
        handler.send_header("Content-Length", str(len(payload)))
        handler.end_headers()
        handler.wfile.write(payload)


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        source = query.get("source", [""])[0]
        if not source:
            _form_response(self)
            return
        if not source.startswith(("http://", "https://")):
            _response(self, 400, "source must be an HTTP or HTTPS URL\n")
            return

        origin = query.get("origin", ["bottom"])[0]
        if origin not in {"bottom", "top"}:
            _response(self, 400, "origin must be 'bottom' or 'top'\n")
            return

        fill = query.get("fill", [" "])[0]
        try:
            grid = parse_html(load_html(source))
            result = render(grid, origin=origin, fill=fill)
        except requests.HTTPError as error:
            status = error.response.status_code if error.response is not None else 502
            if status == 404:
                message = (
                    "Google Docs URL not found. Check that the document is published "
                    "to the web and that the URL is complete.\n"
                )
                _response(self, 404, message)
            else:
                _response(self, 502, f"Unable to fetch source URL (HTTP {status}).\n")
            return
        except Exception as error:
            if isinstance(error, ValueError) and "No coordinate data found" in str(error):
                details = {
                    "error": "The published document contains no coordinate data.",
                    "expected": "A table with x-coordinate, Character, y-coordinate columns",
                    "example": ["0 A 0", "1 B 0", "0 C 1"],
                    "next_step": "Add coordinate rows to Google Docs and publish it again.",
                }
                _response(self, 422, json.dumps(details) + "\n")
            else:
                _response(self, 502, json.dumps({"error": str(error)}) + "\n")
            return

        _response(self, 200, result + "\n")