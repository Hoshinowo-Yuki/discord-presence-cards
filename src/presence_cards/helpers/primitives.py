"""
The MIT License (MIT)

Copyright (c) 2026 Hoshino Yuki

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

# SPDX-License-Identifier: MIT

import base64
import unicodedata
import httpx
from xml.sax.saxutils import escape
from functools import lru_cache
from presence_cards import FONT_DIR
from ..themes import Theme

# A transparent 1x1 PNG, used when an image fetch fails so the card still renders.
FALLBACK_PNG_URI = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwC"
    "AAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

FONT_STACK = "'gg sans', Segoe UI, Helvetica, Arial, sans-serif"

@lru_cache(maxsize=1)
def fontFaceDefs() -> str:
    """
    Build @font-face defs embedding gg sans as base64, cached after first call.

    Embeds the regular and bold weights so the SVG is self-contained. The
    faces use ``font-display:swap`` so text renders immediately in the
    fallback stack and upgrades to gg sans once decoded; it is never
    invisible (no FOIT).

    Returns
    -------
    str
        A <defs> block containing the @font-face <style> rules.
    """

    faces = []

    for fileName, weight in (("ggsans.woff2", 400), ("ggsansbold.woff2", 700)):
        encoded = base64.b64encode((FONT_DIR / fileName).read_bytes()).decode("ascii")
        faces.append(
            f'@font-face{{font-family:"gg sans";'
            f'src:url(data:font/woff2;base64,{encoded}) format("woff2");'
            f'font-weight:{weight};font-style:normal;'
            f'font-display:swap;}}'
        )

    return f'<defs><style>{"".join(faces)}</style></defs>'


def estimateTextWidth(text: str, fontSize: int) -> int:
    """
    Approximate rendered text width without a font engine.

    Full-width and wide glyphs (CJK, etc.) are counted as ~1.0em and
    everything else as ~0.6em. It is a heuristic, but it is CJK-correct.

    Parameters
    ----------
    text : str
        The text to measure.
    fontSize : int
        The font size in pixels, treated as 1em.

    Returns
    -------
    int
        The estimated width in pixels.
    """

    total = 0.0

    for ch in text:
        eastAsianWidth = unicodedata.east_asian_width(ch)
        total += fontSize * (1.0 if eastAsianWidth in ("W", "F") else 0.6)

    return int(total)


def escapeXml(value: str) -> str:
    """
    Escape a string for safe insertion into SVG text nodes.

    Parameters
    ----------
    value : str
        The string to escape. A falsy value is treated as "".

    Returns
    -------
    str
        The XML-escaped string.
    """

    return escape(value or "")


async def fetchDataUri(url: str, httpClient: httpx.AsyncClient) -> str:
    """
    Fetch an image and return it as a base64 data URI.

    Inlining the image keeps the SVG self-contained. On any HTTP error the
    transparent fallback PNG is returned so the card still renders.

    Parameters
    ----------
    url : str
        The image URL to fetch.
    httpClient : httpx.AsyncClient
        The async client used to perform the request.

    Returns
    -------
    str
        The image as a "data:<mime>;base64,..." URI, or `FALLBACK_PNG_URI`
        if the fetch fails.
    """

    try:
        response = await httpClient.get(url, timeout=5.0)
        response.raise_for_status()

    except httpx.HTTPError:
        return FALLBACK_PNG_URI

    mimeType = response.headers.get("content-type", "image/png")
    encoded = base64.b64encode(response.content).decode("ascii")

    return f"data:{mimeType};base64,{encoded}"


def buildText(
    x: int,
    y: int,
    content: str,
    fill: str,
    size: int,
    weight: str = "400",
) -> str:
    """
    Build an SVG <text> node.

    Content is escaped here so callers do not have to.

    Parameters
    ----------
    x : int
        The x-coordinate of the text anchor.
    y : int
        The y-coordinate of the text baseline.
    content : str
        The text content; escaped internally.
    fill : str
        The text fill color.
    size : int
        The font size in pixels.
    weight : str, optional
        The font weight (default is "400").

    Returns
    -------
    str
        The SVG <text> element.
    """

    return (
        f'<text x="{x}" y="{y}" fill="{fill}" '
        f'font-family="{FONT_STACK}" font-size="{size}" '
        f'font-weight="{weight}">{escapeXml(content)}</text>'
    )


def buildCardBackground(theme: Theme, defsId: str = "cardBg") -> tuple[str, str]:
    """
    Build the defs and fill for a card background.

    A flat theme yields no defs and a solid hex fill. A gradient theme
    yields a <linearGradient> in the defs and a matching url(#id) fill.

    Parameters
    ----------
    theme : Theme
        The theme mapping; uses "bgGradient" (a (top, bottom) pair) when
        present, otherwise "background".
    defsId : str, optional
        The id for the generated gradient (default is "cardBg").

    Returns
    -------
    tuple of (str, str)
        The defs markup and the fill value. For a flat theme this is
        ("", "#hex"); for a gradient theme, ("<defs>...</defs>", "url(#id)").
    """

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
    """
    Wrap body markup in the root <svg> element, embedding fonts once.

    This is the single source of truth for the SVG envelope: every renderer
    goes through here, so font embedding can never be forgotten by a new
    layout. All parameters are keyword-only.

    Parameters
    ----------
    width : int
        The SVG width in pixels.
    height : int
        The SVG height in pixels.
    viewBox : str
        The SVG viewBox attribute value.
    body : str
        The inner markup to wrap.

    Returns
    -------
    str
        The complete root <svg> element with fonts embedded.
    """

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="{viewBox}">'
        f'{fontFaceDefs()}{body}'
        f'</svg>'
    )
