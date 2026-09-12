# SPDX-License-Identifier: MIT
"""Generic SVG/text primitives shared by every renderer."""

import base64
import unicodedata
from xml.sax.saxutils import escape

from functools import lru_cache
from pathlib import Path

import httpx

# A transparent 1x1 PNG, used when an image fetch fails so the card still renders.
FALLBACK_PNG_URI = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwC"
    "AAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

FONT_STACK = "'gg sans', Segoe UI, Helvetica, Arial, sans-serif"

_FONT_DIR = Path(__file__).parent.parent.parent / "assets" / "fonts"

@lru_cache(maxsize=1)
def fontFaceDefs() -> str:
    """Embed gg sans (regular + bold) as base64 @font-face, so the SVG is self-contained.

    font-display:swap → text renders immediately in the fallback stack and upgrades
    to gg sans once decoded; it is never invisible (no FOIT)."""
    faces = []
    for fname, weight in (("ggsans.woff2", 400), ("ggsansbold.woff2", 700)):
        b64 = base64.b64encode((_FONT_DIR / fname).read_bytes()).decode("ascii")
        faces.append(
            f'@font-face{{font-family:"gg sans";'
            f'src:url(data:font/woff2;base64,{b64}) format("woff2");'
            f'font-weight:{weight};font-style:normal;'
            f'font-display:swap;}}'
        )
    return f'<defs><style>{"".join(faces)}</style></defs>'

def estimateTextWidth(text: str, fontSize: int) -> int:
    """Approximate rendered text width without a font engine.

    Full-width / wide glyphs (CJK, etc.) count as ~1.0em; everything else
    as ~0.6em. A heuristic, but it's CJK-correct.
    """
    total = 0.0
    for ch in text:
        eaw = unicodedata.east_asian_width(ch)
        total += fontSize * (1.0 if eaw in ("W", "F") else 0.6)
    return int(total)


def escapeXml(value: str) -> str:
    """Escape a string for safe insertion into SVG text nodes."""
    return escape(value or "")


async def fetchDataUri(url: str, httpClient: httpx.AsyncClient) -> str:
    """Fetch an image and return it as a base64 data URI so the SVG is self-contained."""
    try:
        response = await httpClient.get(url, timeout=5.0)
        response.raise_for_status()
    except httpx.HTTPError:
        return FALLBACK_PNG_URI

    mime = response.headers.get("content-type", "image/png")
    encoded = base64.b64encode(response.content).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def buildText(
    x: int,
    y: int,
    content: str,
    fill: str,
    size: int,
    weight: str = "400",
) -> str:
    """Build an SVG <text> node. Content is escaped here so callers don't have to."""
    return (
        f'<text x="{x}" y="{y}" fill="{fill}" '
        f'font-family="{FONT_STACK}" font-size="{size}" '
        f'font-weight="{weight}">{escapeXml(content)}</text>'
    )

def buildCardBackground(theme, defsId: str = "cardBg") -> tuple[str, str]:
    """Return (defsMarkup, fill) for a card background.
    Flat theme → ("", "#hex"). Gradient theme → (<defs>…</defs>, "url(#id)")."""
    gradient = theme.get("bgGradient")
    if not gradient:
        return "", theme["background"]
    top, bottom = gradient
    defs = (
        f'<defs><linearGradient id="{defsId}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0%" stop-color="{top}"/>'
        f'<stop offset="100%" stop-color="{bottom}"/>'
        f'</linearGradient></defs>'
    )
    return defs, f"url(#{defsId})"

def buildSvgRoot(*, width: int, height: int, viewBox: str, body: str) -> str:
    """Wrap body markup in the root <svg> element, embedding fonts once.

    Single source of truth for the SVG envelope: every renderer goes through
    here, so font embedding can never be forgotten by a new layout.

    All parameters are keyword-only (the leading ``*``)."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="{viewBox}">'
        f'{fontFaceDefs()}{body}'
        f'</svg>'
    )