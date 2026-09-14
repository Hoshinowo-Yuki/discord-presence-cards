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
from .status import buildStatusIndicator


def buildAvatarCircle(
    avatarUri: str,
    cx: int,
    cy: int,
    radius: int,
    status: str,
    backgroundColor: str,
    *,
    ringColor: Optional[str] = None,
    decoUri: Optional[str] = None,
    decoScale: float = 1.18,
    ringWidth: int = 0,
    clipId: str = "avatarClip",
) -> str:
    """
    Build a circular avatar with a Discord-accurate status indicator.

    The avatar is clipped to a circle with a status dot at its lower-right
    edge. Two optional extras, used by the profile card, layer on top: a
    ring behind the avatar to separate it from a banner, and an avatar
    decoration overlaid on top.

    Parameters
    ----------
    avatarUri : str
        The URI for the avatar image.
    cx : int
        The x-coordinate of the avatar circle's center.
    cy : int
        The y-coordinate of the avatar circle's center.
    radius : int
        The radius of the avatar circle in pixels.
    status : str
        The user's status, passed through to the status indicator
        (e.g. "online", "idle", "dnd", "offline").
    backgroundColor : str
        The card background color. Passed to the status indicator for its
        gap and punch-out negative space, and used as the default fill for
        the separator ring (see `ringColor`).
    ringColor : Optional[str], optional
        The fill color for the separator ring drawn behind the avatar (only
        when `ringWidth` is set). When None, falls back to
        `backgroundColor`, which is the common case where the ring is meant
        to blend into the card. Set this explicitly only to give the ring a
        distinct color (e.g. an accent). Defaults to None.
    decoUri : Optional[str], optional
        The URI for an avatar decoration (APNG preset) overlaid on the
        avatar. When absent, no decoration is drawn. Defaults to None.
    decoScale : float, optional
        The size of the decoration relative to the avatar diameter
        (default is 1.18).
    ringWidth : int, optional
        The width in pixels of the separator ring drawn behind the avatar.
        When 0, no ring is drawn (default is 0).
    clipId : str, optional
        The id for the avatar's SVG clip path (default is "avatarClip").

    Returns
    -------
    str
        The concatenated SVG elements for the avatar, including the clip
        path, optional ring, image, optional decoration, and status dot.
    """

    size = radius * 2
    x = cx - radius
    y = cy - radius

    parts = [
        f'<defs><clipPath id="{clipId}">'
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" />'
        f'</clipPath></defs>'
    ]

    if ringWidth:
        separatorColor = ringColor if ringColor is not None else backgroundColor
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{radius + ringWidth}" fill="{separatorColor}" />'
        )

    parts.append(
        f'<image href="{avatarUri}" x="{x}" y="{y}" width="{size}" height="{size}" '
        f'clip-path="url(#{clipId})" />'
    )

    if decoUri:
        # Discord avatar decorations are designed to overflow the avatar circle 
        # (decoScale > 1). Clipping to the avatar would defeat decoScale
        # by cropping exactly the overflow it adds.
        #
        # This behavior is intentional.
        dSize = int(size * decoScale)
        dx = cx - dSize // 2
        dy = cy - dSize // 2
        parts.append(
            f'<image href="{decoUri}" x="{dx}" y="{dy}" '
            f'width="{dSize}" height="{dSize}" />'
        )

    # Indicator sits at the lower-right edge of the avatar circle.
    dotCx = cx + int(radius * 0.72)
    dotCy = cy + int(radius * 0.72)
    dotRadius = max(6, int(radius * 0.2))
    parts.append(
        buildStatusIndicator(dotCx, dotCy, dotRadius, status, backgroundColor)
    )

    return "".join(parts)