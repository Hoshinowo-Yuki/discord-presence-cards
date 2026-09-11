# SPDX-License-Identifier: MIT

from datetime import datetime, timezone
from tracemalloc import start
from typing import Optional

from .primitives import buildText


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

def buildGamepadIcon(x: int, y: int, *, color: str, size: int = 15) -> str:
    """Discord's controller glyph as a path, scaled to `size` px, top-left at (x,y)."""
    scale = size / 24  # the path is authored in a 24-unit box
    return (
        f'<path transform="translate({x} {y}) scale({scale:.5f})" '
        f'fill="{color}" fill-rule="evenodd" clip-rule="evenodd" '
        f'd="{_GAMEPAD_PATH}" />'
    )

def _fmt(elapsed: int) -> str:
    h, rem = divmod(elapsed, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def buildAnimatedTimer(
    x: int,
    y: int,
    start: datetime,
    *,
    color: str,
    frames: int = 60,      # how many seconds of flip-book to bake
    size: int = 20,
    weight: str = "600",
) -> str:
    """A SMIL flip-book counter: `frames` stacked <text>s, one per second.

    Each is hidden except during its 1-second window, so the timer ticks
    without scripts — works as an <img> and through GitHub's camo proxy.
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
        isLast = i == frames - 1

        if i == 0:
            initial = "1"
            # don't hide the first frame if it's ALSO the last (frames==1)
            sets = "" if isLast else \
                '<set attributeName="opacity" to="0" begin="1s" fill="freeze"/>'
        else:
            initial = "0"
            show = f'<set attributeName="opacity" to="1" begin="{i}s" fill="freeze"/>'
            hide = "" if isLast else \
                f'<set attributeName="opacity" to="0" begin="{i + 1}s" fill="freeze"/>'
            sets = show + hide

        parts.append(
            f'<text style="{style}" x="{x}" y="{y}" opacity="{initial}">'
            f'{label}{sets}</text>'
        )

    return "".join(parts)


def buildActivityCard(
    x: int,
    y: int,
    width: int,
    height: int,
    *,
    fill: str,
    radius: int = 8,
    padding: int = 12,
) -> tuple[str, int, int, int]:
    """A rounded panel that sits behind the activity row.

    Returns (svg, innerX, innerY, innerWidth) so the caller can lay the
    row out INSIDE the padding instead of re-guessing the offsets.
    """
    rect = (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
        f'rx="{radius}" ry="{radius}" fill="{fill}" />'
    )
    return rect, x + padding, y + padding, width - padding * 2

def buildActivityCard(
    x: int, y: int, width: int, height: int,
    *, fill: str, radius: int = 12, padding: int = 14,
) -> tuple[str, int, int, int]:
    """Rounded panel behind the activity row.
    Returns (svg, innerX, innerY, innerWidth)."""
    rect = (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
        f'rx="{radius}" ry="{radius}" fill="{fill}" />'
    )
    return rect, x + padding, y + padding, width - padding * 2


def buildActivityRow(
    x: int,
    y: int,
    name: str,
    *,
    art: int = 72,           # ← was hardcoded inside; now injectable, default preserves behavior
    textColor: str,
    subTextColor: str,
    accentColor: str,
    ringColor: str,
    details: Optional[str] = None,
    start: Optional[datetime] = None,
    largeUri: Optional[str] = None,
    smallUri: Optional[str] = None,
    clipId: str = "activityArtClip",
) -> str:
    """Activity row: art + badge on the left, up to 3 text lines on the right."""
    parts: list[str] = []                    # ← removed `art = 72`

    if largeUri:
        parts.append(
            f'<defs><clipPath id="{clipId}"><rect x="{x}" y="{y}" '
            f'width="{art}" height="{art}" rx="12" /></clipPath></defs>'
            f'<image href="{largeUri}" x="{x}" y="{y}" width="{art}" '
            f'height="{art}" preserveAspectRatio="xMidYMid slice" '
            f'clip-path="url(#{clipId})" />'
        )
    else:
        parts.append(
            f'<rect x="{x}" y="{y}" width="{art}" height="{art}" rx="12" '
            f'fill="{accentColor}" opacity="0.25" />'
        )

    if smallUri:
        badge = int(art * 0.38)
        bx, by = x + art - badge, y + art - badge
        cx, cy = bx + badge // 2, by + badge // 2
        r = badge // 2
        parts.append(
            f'<defs><clipPath id="{clipId}Small">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" /></clipPath></defs>'
            f'<circle cx="{cx}" cy="{cy}" r="{r + 3}" fill="{ringColor}" />'
            f'<image href="{smallUri}" x="{bx}" y="{by}" '
            f'width="{badge}" height="{badge}" '
            f'preserveAspectRatio="xMidYMid slice" '
            f'clip-path="url(#{clipId}Small)" />'
        )

    textX = x + art + 16                     # already derives from art ✓
    lineY = y + 20
    parts.append(buildText(x=textX, y=lineY, content=name,
                           fill=textColor, size=18, weight="700"))
    lineY += 24

    if details:
        parts.append(buildText(x=textX, y=lineY, content=details,
                               fill=subTextColor, size=15, weight="400"))
        lineY += 22

    if start is not None:
        parts.append(buildGamepadIcon(textX, lineY - 12, color=accentColor, size=15))
        parts.append(buildAnimatedTimer(
            x=textX + 20, y=lineY, start=start,
            color=accentColor, size=15, weight="600",
        ))

    return "".join(parts)