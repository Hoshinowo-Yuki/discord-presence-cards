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

from typing import Optional
from presence_cards.store import Presence
from .primitives import FONT_STACK, buildText, escapeXml, estimateTextWidth
from ..themes import Theme


def _buildFlagBadges(
    badgeUris: list[str],
    size: int = 30,
    gap: int = 4
) -> str:
    """
    Build an inline-flex group of flag badges for the foreignObject row.

    The badges are grouped in their own flex container so their internal
    gap stays tight, independent of the surrounding row's 8px gap.

    Parameters
    ----------
    badgeUris : list of str
        The data-URI SVGs for each flag badge. An empty list yields "".
    size : int, optional
        The width and height of each badge in pixels (default is 30).
    gap : int, optional
        The gap between badges within the group in pixels (default is 4).

    Returns
    -------
    str
        The XHTML for the badge group, or "" when `badgeUris` is empty.
    """

    if not badgeUris:
        return ""

    images = "".join(
        f'<img src="{uri}" width="{size}" height="{size}" style="display:block" />'
        for uri in badgeUris
    )

    return (
        f'<div style="display:inline-flex;align-items:center;gap:{gap}px">'
        f'{images}</div>'
    )


def buildStatusPill(
    text: Optional[str],
    emojiUnicode: Optional[str],
    emojiUrl: Optional[str],
    theme: Theme,
    emojiSize: int = 28,
    maxHeight: int = 85,
) -> str:
    """
    Build a custom-status bubble matching Discord.

    Renders a rounded rectangle with the emoji on the left (top-aligned to
    the first line) and italic text wrapping to at most two lines. There is
    no tail. Returns "" when there is nothing to show.

    Parameters
    ----------
    text : Optional[str]
        The status text. May be None or empty.
    emojiUnicode : Optional[str]
        A Unicode emoji for the status, used when `emojiUrl` is absent.
    emojiUrl : Optional[str]
        A URL for a custom emoji image, which takes precedence over
        `emojiUnicode`.
    theme : Theme
        The theme mapping; uses "tagPill" for the background and "subtext"
        for the text color.
    emojiSize : int, optional
        The emoji width and height in pixels (default is 28).
    maxHeight : int, optional
        The maximum bubble height in pixels before overflow is clipped
        (default is 85).

    Returns
    -------
    str
        The XHTML for the status bubble, or "" when `text`, `emojiUnicode`,
        and `emojiUrl` are all falsy.
    """

    if not (text or emojiUnicode or emojiUrl):
        return ""

    if emojiUrl:
        emojiEl = (
            f'<img src="{emojiUrl}" width="{emojiSize}" height="{emojiSize}" '
            f'style="display:block;flex:none;border-radius:50%" />'
        )
    elif emojiUnicode:
        emojiEl = (
            f'<span style="font-family:{FONT_STACK};flex:none;'
            f'font-size:{emojiSize}px;line-height:26px">{escapeXml(emojiUnicode)}</span>'
        )
    else:
        emojiEl = ""

    textEl = (
        f'<span style="font:italic 400 20px {FONT_STACK};'
        f'color:{theme["subtext"]};min-width:0;'
        f'overflow-wrap:anywhere">'
        f'{escapeXml(text)}</span>'
        if text else ""
    )

    return (
        f'<div xmlns="http://www.w3.org/1999/xhtml" '
        f'style="display:inline-flex;align-items:flex-start;gap:12px;'
        f'padding:16px 22px;border-radius:20px;background:{theme["tagPill"]};'
        f'width:max-content;max-width:100%;max-height:{maxHeight}px;'
        f'box-sizing:border-box;overflow:hidden">'
        f'{emojiEl}{textEl}</div>'
    )


def buildServerTagPill(
    x: int,
    cy: int,
    tagText: str,
    badgeUri: Optional[str],
    textColor: str,
    pillColor: str,
) -> tuple[str, int]:
    """
    Build a native-SVG server-tag pill in the form [badge] TAG.

    Parameters
    ----------
    x : int
        The x-coordinate of the pill's left edge.
    cy : int
        The y-coordinate of the pill's vertical center.
    tagText : str
        The tag text shown after the optional badge.
    badgeUri : Optional[str]
        The URI for a leading badge image. When None, no badge is drawn and
        its width and gap collapse to zero.
    textColor : str
        The color of the tag text.
    pillColor : str
        The fill color of the pill background.

    Returns
    -------
    tuple of (str, int)
        The pill's SVG markup and its total width in pixels, so callers can
        position content after it.
    """

    paddingX = 8
    fontSize = 13
    pillHeight = 22
    badgeSize = 16 if badgeUri else 0
    badgeGap = 4 if badgeUri else 0

    textWidth = estimateTextWidth(tagText, fontSize)
    pillWidth = paddingX * 2 + badgeSize + badgeGap + textWidth
    top = cy - pillHeight // 2

    parts = [
        f'<rect x="{x}" y="{top}" width="{pillWidth}" '
        f'height="{pillHeight}" rx="{pillHeight // 2}" fill="{pillColor}" />'
    ]

    contentX = x + paddingX
    if badgeUri:
        parts.append(
            f'<image href="{badgeUri}" x="{contentX}" y="{cy - badgeSize // 2}" '
            f'width="{badgeSize}" height="{badgeSize}" />'
        )
        contentX += badgeSize + badgeGap

    parts.append(
        buildText(contentX, cy + fontSize // 2 - 2, tagText, textColor, fontSize, "600")
    )
    return "".join(parts), pillWidth


def buildHandlePillRow(
    x: int,
    y: int,
    width: int,
    height: int,
    presence: Presence,
    theme: Theme,
    badgeUri: Optional[str],
) -> str:
    """
    Build the @handle row with an inline [badge] TAG pill and flag badges.

    Rendered as XHTML inside a <foreignObject>. The box geometry is passed
    in so the row stays independent of any single card's layout constants.

    Parameters
    ----------
    x : int
        The x-coordinate of the foreignObject's left edge.
    y : int
        The y-coordinate of the foreignObject's top edge.
    width : int
        The width of the foreignObject in pixels.
    height : int
        The height of the foreignObject in pixels.
    presence : Presence
        The presence record; supplies the username, server-tag text, and
        flag badge URIs.
    theme : Theme
        The theme mapping; uses "subtext" for the handle, and "tagPill" and
        "text" for the pill.
    badgeUri : Optional[str]
        The URI for the tag pill's leading badge. When None, no badge is
        drawn inside the pill.

    Returns
    -------
    str
        The foreignObject markup for the row.
    """

    handle = escapeXml(f"@{presence.username}") if presence.username else ""
    pill = ""

    if presence.serverTagText:
        badgeImg = (
            f'<img src="{badgeUri}" width="16" height="16" '
            f'style="display:block;border-radius:3px" />'
            if badgeUri else ""
        )
        pill = (
            f'<div style="display:inline-flex;align-items:center;gap:5px;'
            f'padding:4px 14px 4px 11px;border-radius:13px;background:{theme["tagPill"]};'
            f'font:600 16px {FONT_STACK};color:{theme["text"]}">'
            f'{badgeImg}<span>{escapeXml(presence.serverTagText)}</span></div>'
        )

    badges = _buildFlagBadges(presence.badgeUris)

    body = (
        f'<div xmlns="http://www.w3.org/1999/xhtml" '
        f'style="display:flex;align-items:center;gap:8px;font-family:{FONT_STACK}">'
        f'<div style="font:400 20px {FONT_STACK};color:{theme["subtext"]}">{handle}</div>'
        f'{pill}{badges}</div>'
    )

    return (
        f'<foreignObject x="{x}" y="{y}" width="{width}" height="{height}">'
        f'{body}</foreignObject>'
    )
