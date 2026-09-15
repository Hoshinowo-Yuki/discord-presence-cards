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
from .primitives import (
    FONT_STACK,
    build_text,
    escape_xml,
    estimate_text_width,
)
from ..themes import Theme


def _build_flag_badges(
    badge_uris: list[str],
    size: int = 30,
    gap: int = 4
) -> str:
    """
    Build an inline-flex group of flag badges for the foreignObject row.

    The badges are grouped in their own flex container so their internal
    gap stays tight, independent of the surrounding row's 8px gap.

    Parameters
    ----------
    badge_uris : list of str
        The data-URI SVGs for each flag badge. An empty list yields "".
    size : int, optional
        The width and height of each badge in pixels (default is 30).
    gap : int, optional
        The gap between badges within the group in pixels (default is 4).

    Returns
    -------
    str
        The XHTML for the badge group, or "" when `badge_uris` is empty.
    """

    if not badge_uris:
        return ""

    images = "".join(
        f'<img src="{uri}" width="{size}" height="{size}" style="display:block" />'
        for uri in badge_uris
    )

    return (
        f'<div style="display:inline-flex;align-items:center;gap:{gap}px">'
        f'{images}</div>'
    )


def build_status_pill(
    text: Optional[str],
    emoji_unicode: Optional[str],
    emoji_url: Optional[str],
    theme: Theme,
    emoji_size: int = 28,
    max_height: int = 85,
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
    emoji_unicode : Optional[str]
        A Unicode emoji for the status, used when `emoji_url` is absent.
    emoji_url : Optional[str]
        A URL for a custom emoji image, which takes precedence over
        `emoji_unicode`.
    theme : Theme
        The theme mapping; uses "tag_pill" for the background and "subtext"
        for the text color.
    emoji_size : int, optional
        The emoji width and height in pixels (default is 28).
    max_height : int, optional
        The maximum bubble height in pixels before overflow is clipped
        (default is 85).

    Returns
    -------
    str
        The XHTML for the status bubble, or "" when `text`, `emoji_unicode`,
        and `emoji_url` are all falsy.
    """

    if not (text or emoji_unicode or emoji_url):
        return ""

    if emoji_url:
        emoji_el = (
            f'<img src="{emoji_url}" width="{emoji_size}" height="{emoji_size}" '
            f'style="display:block;flex:none;border-radius:50%" />'
        )
    elif emoji_unicode:
        emoji_el = (
            f'<span style="font-family:{FONT_STACK};flex:none;'
            f'font-size:{emoji_size}px;line-height:26px">{escape_xml(emoji_unicode)}</span>'
        )
    else:
        emoji_el = ""

    text_el = (
        f'<span style="font:italic 400 20px {FONT_STACK};'
        f'color:{theme["subtext"]};min-width:0;'
        f'overflow-wrap:anywhere">'
        f'{escape_xml(text)}</span>'
        if text else ""
    )

    return (
        f'<div xmlns="http://www.w3.org/1999/xhtml" '
        f'style="display:inline-flex;align-items:flex-start;gap:12px;'
        f'padding:16px 22px;border-radius:20px;background:{theme["tag_pill"]};'
        f'width:max-content;max-width:100%;max-height:{max_height}px;'
        f'box-sizing:border-box;overflow:hidden">'
        f'{emoji_el}{text_el}</div>'
    )


def build_server_tag_pill(
    x: int,
    cy: int,
    tag_text: str,
    badge_uri: Optional[str],
    text_color: str,
    pill_color: str,
) -> tuple[str, int]:
    """
    Build a native-SVG server-tag pill in the form [badge] TAG.

    Parameters
    ----------
    x : int
        The x-coordinate of the pill's left edge.
    cy : int
        The y-coordinate of the pill's vertical center.
    tag_text : str
        The tag text shown after the optional badge.
    badge_uri : Optional[str]
        The URI for a leading badge image. When None, no badge is drawn and
        its width and gap collapse to zero.
    text_color : str
        The color of the tag text.
    pill_color : str
        The fill color of the pill background.

    Returns
    -------
    tuple of (str, int)
        The pill's SVG markup and its total width in pixels, so callers can
        position content after it.
    """

    padding_x = 8
    font_size = 13
    pill_height = 22
    badge_size = 16 if badge_uri else 0
    badge_gap = 4 if badge_uri else 0

    text_width = estimate_text_width(tag_text, font_size)
    pill_width = padding_x * 2 + badge_size + badge_gap + text_width
    top = cy - pill_height // 2

    parts = [
        f'<rect x="{x}" y="{top}" width="{pill_width}" '
        f'height="{pill_height}" rx="{pill_height // 2}" fill="{pill_color}" />'
    ]

    content_x = x + padding_x
    if badge_uri:
        parts.append(
            f'<image href="{badge_uri}" x="{content_x}" y="{cy - badge_size // 2}" '
            f'width="{badge_size}" height="{badge_size}" />'
        )
        content_x += badge_size + badge_gap

    parts.append(
        build_text(content_x, cy + font_size // 2 - 2, tag_text, text_color, font_size, "600")
    )
    return "".join(parts), pill_width


def build_handle_pill_row(
    x: int,
    y: int,
    width: int,
    height: int,
    presence: Presence,
    theme: Theme,
    badge_uri: Optional[str],
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
        The theme mapping; uses "subtext" for the handle, and "tag_pill" and
        "text" for the pill.
    badge_uri : Optional[str]
        The URI for the tag pill's leading badge. When None, no badge is
        drawn inside the pill.

    Returns
    -------
    str
        The foreignObject markup for the row.
    """

    handle = escape_xml(f"@{presence.username}") if presence.username else ""
    pill = ""

    if presence.server_tag_text:
        badge_size = 16
        badge_img = (
            f'<img src="{badge_uri}" width="{badge_size}" height="{badge_size}" '
            f'style="display:block;border-radius:3px" />'
            if badge_uri else ""
        )

        pill = (
            f'<div style="display:inline-flex;align-items:center;gap:5px;'
            f'padding:4px 14px 4px 11px;border-radius:13px;background:{theme["tag_pill"]};'
            f'font:600 16px {FONT_STACK};color:{theme["text"]}">'
            f'{badge_img}<span>{escape_xml(presence.server_tag_text)}</span></div>'
        )

    badges = _build_flag_badges(presence.badge_uris)

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
