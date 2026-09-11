# SPDX-License-Identifier: MIT
"""Circular avatar with optional decoration ring + status indicator."""

from typing import Optional

from .status import buildStatusIndicator


def buildAvatarCircle(
    avatarUri: str,
    cx: int,
    cy: int,
    radius: int,
    status: str,
    ringColor: str,
    *,
    decoUri: Optional[str] = None,
    decoScale: float = 1.18,
    ringWidth: int = 0,
    clipId: str = "avatarClip",
) -> str:
    """Build a circular avatar with a Discord-accurate status indicator.

    Optional extras (used by the profile card):
      * `ringWidth` draws a background-coloured ring behind the avatar,
        separating it from a banner.
      * `decoUri` overlays an avatar decoration (APNG preset), scaled by
        `decoScale` relative to the avatar diameter.
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
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{radius + ringWidth}" fill="{ringColor}" />'
        )

    parts.append(
        f'<image href="{avatarUri}" x="{x}" y="{y}" width="{size}" height="{size}" '
        f'clip-path="url(#{clipId})" />'
    )

    if decoUri:
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
        buildStatusIndicator(dotCx, dotCy, dotRadius, status, ringColor)
    )

    return "".join(parts)