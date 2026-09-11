# SPDX-License-Identifier: MIT
"""Single source of truth for presence status: colour AND shape."""

# Discord-style status colours, keyed by presence status.
STATUS_COLORS: dict[str, str] = {
    "online": "#43b581",
    "idle": "#faa61a",
    "dnd": "#f04747",
    "offline": "#747f8d",
}


def resolveStatusColor(status: str) -> str:
    return STATUS_COLORS.get(status, STATUS_COLORS["offline"])


def buildStatusIndicator(
    cx: int,
    cy: int,
    radius: int,
    status: str,
    ringColor: str,
) -> str:
    """Build a Discord-accurate status indicator.

    Each status is a distinct SHAPE, not just a colour:
      online  -> solid filled circle
      idle    -> crescent (circle with an offset cutout)
      dnd     -> circle with a horizontal bar punched through
      offline -> hollow ring (donut)

    `ringColor` is the card background — used both for the gap around the
    indicator and to 'punch out' the negative space inside each shape.
    Colour is resolved here from `status`, so shape and colour can't drift.
    """
    color = resolveStatusColor(status)

    # Background circle creates the gap between the avatar edge and the dot,
    # exactly like Discord separating the indicator from the avatar ring.
    gap = 4
    backdrop = f'<circle cx="{cx}" cy="{cy}" r="{radius + gap}" fill="{ringColor}" />'

    if status == "online":
        shape = f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}" />'

    elif status == "idle":
        cutCx = cx - int(radius * 0.45)
        cutCy = cy - int(radius * 0.45)
        shape = (
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}" />'
            f'<circle cx="{cutCx}" cy="{cutCy}" r="{int(radius * 0.85)}" fill="{ringColor}" />'
        )

    elif status == "dnd":
        barW = radius * 1.3
        barH = max(2.0, radius * 0.45)
        shape = (
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}" />'
            f'<rect x="{cx - barW / 2}" y="{cy - barH / 2}" '
            f'width="{barW}" height="{barH}" rx="{barH / 2}" fill="{ringColor}" />'
        )

    else:  # offline / invisible -> hollow ring
        shape = (
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}" />'
            f'<circle cx="{cx}" cy="{cy}" r="{int(radius * 0.5)}" fill="{ringColor}" />'
        )

    return backdrop + shape