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

# Discord-style status colours, keyed by presence status.
STATUS_COLORS: dict[str, str] = {
    "online": "#43b581",
    "idle": "#faa61a",
    "dnd": "#f04747",
    "offline": "#747f8d",
}


def resolve_status_color(status: str) -> str:
    """
    Resolve a presence status to its Discord-style color.

    Parameters
    ----------
    status : str
        The presence status (e.g. "online", "idle", "dnd", "offline").

    Returns
    -------
    str
        The hex color for the status, falling back to the offline color for
        an unknown status.
    """
    return STATUS_COLORS.get(status, STATUS_COLORS["offline"])


def build_status_indicator(
    cx: int,
    cy: int,
    radius: int,
    status: str,
    background_color: str,
) -> str:
    """
    Build a Discord-accurate status indicator.

    Each status is a distinct shape, not just a color::

        online  -> solid filled circle
        idle    -> crescent (circle with an offset cutout)
        dnd     -> circle with a horizontal bar punched through
        offline -> hollow ring (donut)

    The color is resolved here from `status`, so shape and color cannot
    drift out of sync.

    Parameters
    ----------
    cx : int
        The x-coordinate of the indicator's center.
    cy : int
        The y-coordinate of the indicator's center.
    radius : int
        The radius of the indicator in pixels.
    status : str
        The presence status, which selects both the shape and the color.
    background_color : str
        The card background color. Used both for the gap around the
        indicator (the backdrop circle) and to punch out the negative
        space inside each shape, so the card shows through.

    Returns
    -------
    str
        The SVG markup for the backdrop plus the status shape.
    """

    color = resolve_status_color(status)

    # Background circle creates the gap between the avatar edge and the dot,
    # exactly like Discord separating the indicator from the avatar ring.
    gap = max(2, int(radius * 0.5625))
    backdrop = f'<circle cx="{cx}" cy="{cy}" r="{radius + gap}" fill="{background_color}" />'

    if status == "online":
        shape = f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}" />'

    elif status == "idle":
        cutout_cx = cx - radius * 0.375
        cutout_cy = cy - radius * 0.3125
        shape = (
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}" />'
            f'<circle cx="{cutout_cx}" cy="{cutout_cy}" r="{radius * 0.75}" fill="{background_color}" />'
        )

    elif status == "dnd":
        bar_width = radius * 1.3
        bar_height = max(2.0, radius * 0.45)
        shape = (
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}" />'
            f'<rect x="{cx - bar_width / 2}" y="{cy - bar_height / 2}" '
            f'width="{bar_width}" height="{bar_height}" rx="{bar_height / 2}" fill="{background_color}" />'
        )

    else:  # offline / invisible -> hollow ring
        shape = (
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}" />'
            f'<circle cx="{cx}" cy="{cy}" r="{int(radius * 0.5)}" fill="{background_color}" />'
        )

    return backdrop + shape