"""Step 1 - Fetch HTML from a URL (Google Docs or web) or a local file."""
from __future__ import annotations

import logging
import re
from pathlib import Path

import requests

log = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (GridDecoder/1.0; +python-requests)"
_GDOC_EDIT = re.compile(r"(https://docs\.google\.com/document/d/)([\w-]+)(/.*)?$")


def normalize_url(url: str) -> str:
    """Convert a Google Docs /edit link to /export?format=html for raw HTML.

    - Keep 'Publish to the web' links (/d/e/.../pub) unchanged.
    - Convert /d/<id>/edit to /d/<id>/export?format=html (the document must be public).
    """
    if "/document/d/e/" in url:  # Already published link.
        return url
    m = _GDOC_EDIT.match(url)
    if m:
        new = f"{m.group(1)}{m.group(2)}/export?format=html"
        log.debug("Normalized Google Docs URL: %s", new)
        return new
    return url


def load_html(source: str, timeout: float = 20.0) -> bytes:
    """Return HTML as bytes; BeautifulSoup will detect the encoding automatically."""
    if source.startswith(("http://", "https://")):
        url = normalize_url(source)
        log.info("Downloading %s", url)
        with requests.Session() as s:  # Close connections through the context manager.
            resp = s.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
            resp.raise_for_status()
            if "text/html" not in resp.headers.get("Content-Type", "text/html"):
                log.warning("Content-Type is not HTML: %s", resp.headers.get("Content-Type"))
            return resp.content

    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {source}")
    log.info("Reading file %s", path)
    return path.read_bytes()
