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

from datetime import datetime, timezone
from typing import Optional
from .primitives import build_text


_GAMEPAD_PATH = (
    "M20.97 4.06c0 .18.08.35.24.43.55.28.9.82 1.04 1.42.3 1.24.75 3.7.75 "
    "7.09v4.91a3.09 3.09 0 0 1-5.85 1.38l-1.76-3.51a1.09 1.09 0 0 0-1.23-.55c"
    "-.57.13-1.36.27-2.16.27s-1.6-.14-2.16-.27c-.49-.11-1 .1-1.23.55l-1.76 "
    "3.51A3.09 3.09 0 0 1 1 17.91V13c0-3.38.46-5.85.75-7.1.15-.6.49-1.13 "
    "1.04-1.4a.47.47 0 0 0 .24-.44c0-.7.48-1.32 1.2-1.47l2.93-.62c.5-.1 1 .06 "
    "1.36.4.35.34.78.71 1.28.68a42.4 42.4 0 0 1 4.4 0c.5.03.93-.34 "
    "1.28-.69.35-.33.86-.5 1.36-.39l2.94.62c.7.15 1.19.78 1.19 1.47ZM20 7.5a1.5 "
    "1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0ZM15.5 12a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 "
    "3ZM5 7a1 1 0 0 1 2 0v1h1a1 1 0 0 1 0 2H7v1a1 1 0 1 1-2 0v-1H4a1 1 0 1 1 "
    "0-2h1V7Z"
)

def build_gamepad_icon(x: int, y: int, *, color: str, size: int = 15) -> str:
    """
    Build an SVG path for a gamepad icon, scaled to the specified size and positioned at (x, y).

    Parameters
    ----------
    x : int
        The x-coordinate for the top-left corner of the icon.
    y : int
        The y-coordinate for the top-left corner of the icon.
    color : str
        The fill color for the icon.
    size : int, optional
        The size of the icon in pixels (default is 15).

    Returns
    -------
    str
        An SVG path for the gamepad icon.

    """

    scale = size / 24  # the path is authored in a 24-unit box
    return (
        f'<path transform="translate({x} {y}) scale({scale:.5f})" '
        f'fill="{color}" fill-rule="evenodd" clip-rule="evenodd" '
        f'd="{_GAMEPAD_PATH}" />'
    )


def _fmt(elapsed: int) -> str:
    """
    Format a duration in seconds as a clock string.

    Parameters
    ----------
    elapsed : int
        The elapsed time in seconds.

    Returns
    -------
    str
        The duration formatted as "H:MM:SS", or "M:SS" when under an hour.
    """

    h, rem = divmod(elapsed, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def build_animated_timer(
    x: int,
    y: int,
    start: datetime,
    *,
    color: str,
    frames: int = 60,
    size: int = 20,
    weight: str = "600",
) -> str:
    """
    Build a script-free animated timer as a SMIL flip-book.

    Bakes `frames` stacked <text> elements, one per second, each hidden
    except during its own one-second window.
    
    This lets the timer tick without JavaScript, so it survives being embedded as an <img> and
    passing through GitHub's camo image proxy.

    Parameters
    ----------
    x : int
        The x-coordinate of the timer's text baseline.
    y : int
        The y-coordinate of the timer's text baseline.
    start : datetime
        The tz-aware start time to count up from. The initial elapsed
        value is computed against the current UTC time and clamped to
        zero if `start` is in the future.
    color : str
        The fill color for the timer text.
    frames : int, optional
        How many seconds of flip-book to bake, i.e. how long the timer
        animates before it stops (default is 60).
    size : int, optional
        The font size in pixels (default is 20).
    weight : str, optional
        The font weight (default is "600").

    Returns
    -------
    str
        The concatenated SVG <text> elements for the animated timer.
    """

    base = int((datetime.now(timezone.utc) - start).total_seconds())
    if base < 0:
        base = 0

    style = (
        f"fill:{color};font-family:GG Sans,sans-serif;"
        f"font-size:{size}px;font-weight:{weight}"
    )

    parts: list[str] = []

    for i in range(frames):
        label = _fmt(base + i)
        is_last = i == frames - 1

        if i == 0:
            initial = "1"
            # don't hide the first frame if it's ALSO the last (frames==1)
            sets = "" if is_last else \
                '<set attributeName="opacity" to="0" begin="1s" fill="freeze"/>'

        else:
            initial = "0"
            show = f'<set attributeName="opacity" to="1" begin="{i}s" fill="freeze"/>'
            hide = "" if is_last else \
                f'<set attributeName="opacity" to="0" begin="{i + 1}s" fill="freeze"/>'
            sets = show + hide

        parts.append(
            f'<text style="{style}" x="{x}" y="{y}" opacity="{initial}">'
            f'{label}{sets}</text>'
        )

    return "".join(parts)


def build_activity_card(
    x: int,
    y: int,
    width: int,
    height: int,
    *,
    fill: str,
    radius: int = 8,
    padding: int = 12,
) -> tuple[str, int, int, int]:
    """
    Build a rounded panel that sits behind the activity row.

    Returns the inner offsets alongside the SVG so the caller can lay the
    row out inside the padding instead of re-deriving the geometry.

    Parameters
    ----------
    x : int
        The x-coordinate of the panel's top-left corner.
    y : int
        The y-coordinate of the panel's top-left corner.
    width : int
        The panel width in pixels.
    height : int
        The panel height in pixels.
    fill : str
        The fill color for the panel.
    radius : int, optional
        The corner radius in pixels (default is 8).
    padding : int, optional
        The inner padding in pixels, inset on all sides (default is 12).

    Returns
    -------
    tuple of (str, int, int, int)
        The panel's SVG <rect>, followed by the inner x, inner y, and
        inner width for laying out content within the padding.
    """

    rect = (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
        f'rx="{radius}" ry="{radius}" fill="{fill}" />'
    )
    return rect, x + padding, y + padding, width - padding * 2


def build_activity_row(
    x: int,
    y: int,
    name: str,
    *,
    art: int = 120,
    text_color: str,
    sub_text_color: str,
    accent_color: str,
    ring_color: str,
    details: Optional[str] = None,
    state: Optional[str] = None,
    start: Optional[datetime] = None,
    large_uri: Optional[str] = None,
    small_uri: Optional[str] = None,
    clip_id: str = "activityArtClip",
) -> str:
    """
    Build an activity row: art and badge on the left, text lines on the right.

    Renders the large activity art (or an accent-tinted placeholder when
    absent), an optional small badge clipped into a ringed circle over its
    corner, and up to three text lines: the activity name, optional details,
    and an optional gamepad icon paired with an animated elapsed timer.

    Parameters
    ----------
    x : int
        The x-coordinate of the row's top-left corner.
    y : int
        The y-coordinate of the row's top-left corner.
    name : str
        The activity name, rendered as the first text line.
    art : int, optional
        The size of the large activity art in pixels. All other offsets
        (badge, text column) derive from this (default is 120).
    text_color : str
        The fill color for the activity name.
    sub_text_color : str
        The fill color for the details line.
    accent_color : str
        The accent color used for the art placeholder, the gamepad icon,
        and the timer.
    ring_color : str
        The fill color for the ring drawn behind the small badge.
    details : Optional[str], optional
        The details line rendered under the name, if any. Defaults to None.
    state : Optional[str], optional
        The state line rendered under the details, if any. Defaults to None.
    start : Optional[datetime], optional
        The tz-aware activity start time. When provided, a gamepad icon and
        animated timer are rendered. Defaults to None.
    large_uri : Optional[str], optional
        The URI for the large activity art. When absent, an accent-tinted
        placeholder is drawn instead. Defaults to None.
    small_uri : Optional[str], optional
        The URI for the small corner badge, if any. Defaults to None.
    clip_id : str, optional
        The base id for the SVG clip paths. The small badge derives its own
        id by appending "Small" (default is "activityArtClip").

    Returns
    -------
    str
        The concatenated SVG elements for the full activity row.
    """

    parts: list[str] = []

    if large_uri:
        parts.append(
            f'<defs><clipPath id="{clip_id}"><rect x="{x}" y="{y}" '
            f'width="{art}" height="{art}" rx="12" /></clipPath></defs>'
            f'<image href="{large_uri}" x="{x}" y="{y}" width="{art}" '
            f'height="{art}" preserveAspectRatio="xMidYMid slice" '
            f'clip-path="url(#{clip_id})" />'
        )
    else:
        parts.append(
            f'<rect x="{x}" y="{y}" width="{art}" height="{art}" rx="12" '
            f'fill="{accent_color}" opacity="0.25" />'
        )

    if small_uri:
        badge = int(art * 0.38)
        bx, by = x + art - badge, y + art - badge
        cx, cy = bx + badge // 2, by + badge // 2
        r = badge // 2
        parts.append(
            f'<defs><clipPath id="{clip_id}Small">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" /></clipPath></defs>'
            f'<circle cx="{cx}" cy="{cy}" r="{r + 3}" fill="{ring_color}" />'
            f'<image href="{small_uri}" x="{bx}" y="{by}" '
            f'width="{badge}" height="{badge}" '
            f'preserveAspectRatio="xMidYMid slice" '
            f'clip-path="url(#{clip_id}Small)" />'
        )

    text_x = x + art + 16
    line_y = y + 24

    parts.append(
        build_text(
            x=text_x,
            y=line_y,
            content=name,
            fill=text_color,
            size=24,
            weight="700"
        )
    )

    line_y += 28

    for line in (details, state):
        if line:
            parts.append(
                build_text(
                    x=text_x,
                    y=line_y,
                    content=line,
                    fill=sub_text_color,
                    size=20,
                    weight="400"
                )
            )

            line_y += 28

    if start is not None:
        parts.append(
            build_gamepad_icon(
                text_x,
                line_y - 12,
                color=accent_color,
                size=15
            )
        )

        parts.append(
            build_animated_timer(
                x=text_x + 20,
                y=line_y,
                start=start,
                color=accent_color,
                size=20,
                weight="600",
            )
        )

    return "".join(parts)
