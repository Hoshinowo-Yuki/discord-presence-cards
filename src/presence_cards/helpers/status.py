# SPDX-License-Identifier: MIT

# Discord-style status colours, keyed by presence status.
STATUS_COLORS: dict[str, str] = {
    "online": "#43b581",
    "idle": "#faa61a",
    "dnd": "#f04747",
    "offline": "#747f8d",
}


def resolveStatusColor(status: str) -> str:
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


def buildStatusIndicator(
    cx: int,
    cy: int,
    radius: int,
    status: str,
    backgroundColor: str,
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
    backgroundColor : str
        The card background color. Used both for the gap around the
        indicator (the backdrop circle) and to punch out the negative
        space inside each shape, so the card shows through.

    Returns
    -------
    str
        The SVG markup for the backdrop plus the status shape.
    """

    color = resolveStatusColor(status)

    # Background circle creates the gap between the avatar edge and the dot,
    # exactly like Discord separating the indicator from the avatar ring.
    gap = max(2, int(radius * 0.5625))
    backdrop = f'<circle cx="{cx}" cy="{cy}" r="{radius + gap}" fill="{backgroundColor}" />'

    if status == "online":
        shape = f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}" />'

    elif status == "idle":
        cutoutCx = cx - radius * 0.375
        cutoutCy = cy - radius * 0.3125
        shape = (
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}" />'
            f'<circle cx="{cutoutCx}" cy="{cutoutCy}" r="{radius * 0.75}" fill="{backgroundColor}" />'
        )

    elif status == "dnd":
        barWidth = radius * 1.3
        barHeight = max(2.0, radius * 0.45)
        shape = (
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}" />'
            f'<rect x="{cx - barWidth / 2}" y="{cy - barHeight / 2}" '
            f'width="{barWidth}" height="{barHeight}" rx="{barHeight / 2}" fill="{backgroundColor}" />'
        )

    else:  # offline / invisible -> hollow ring
        shape = (
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}" />'
            f'<circle cx="{cx}" cy="{cy}" r="{int(radius * 0.5)}" fill="{backgroundColor}" />'
        )

    return backdrop + shape