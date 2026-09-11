# SPDX-License-Identifier: MIT
"""Server-tag pills. Two strategies: native SVG (default card) and
XHTML-in-foreignObject (profile card). They are intentionally separate."""

from typing import Optional

from presence_cards.store import Presence

from .primitives import FONT_STACK, buildText, escapeXml, estimateTextWidth

def _buildFlagBadges(badgeUris: list[str], size: int = 28, gap: int = 4) -> str:
    """Inline-flex group of flag badges (data-URI SVGs) for the foreignObject row.
    Grouped so their internal gap is tight, independent of the row's 8px gap."""
    if not badgeUris:
        return ""
    imgs = "".join(
        f'<img src="{uri}" width="{size}" height="{size}" style="display:block" />'
        for uri in badgeUris
    )
    return (
        f'<div style="display:inline-flex;align-items:center;gap:{gap}px">'
        f'{imgs}</div>'
    )

def buildServerTagPill(
    x: int,
    cy: int,
    tagText: str,
    badgeUri: Optional[str],
    textColor: str,
    pillColor: str,
) -> tuple[str, int]:
    """Native-SVG pill: [badge] TAG.

    Returns (markup, pillWidth) so callers can position content after it.
    """
    padX = 8
    fontSize = 13
    pillH = 22
    badgeSize = 16 if badgeUri else 0
    badgeGap = 4 if badgeUri else 0

    textW = estimateTextWidth(tagText, fontSize)
    pillW = padX * 2 + badgeSize + badgeGap + textW
    top = cy - pillH // 2

    parts = [
        f'<rect x="{x}" y="{top}" width="{pillW}" '
        f'height="{pillH}" rx="{pillH // 2}" fill="{pillColor}" />'
    ]

    contentX = x + padX
    if badgeUri:
        parts.append(
            f'<image href="{badgeUri}" x="{contentX}" y="{cy - badgeSize // 2}" '
            f'width="{badgeSize}" height="{badgeSize}" />'
        )
        contentX += badgeSize + badgeGap

    parts.append(
        buildText(contentX, cy + fontSize // 2 - 2, tagText, textColor, fontSize, "600")
    )
    return "".join(parts), pillW


def buildHandlePillRow(
    x: int,
    y: int,
    width: int,
    height: int,
    presence: Presence,
    theme: dict,
    badgeUri: Optional[str],
) -> str:
    """XHTML row inside <foreignObject>: @handle with an inline [badge] TAG pill.

    Box geometry (x/y/width/height) is passed in so this stays independent of
    any single card's layout constants.
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
            f'padding:4px 11px;border-radius:13px;background:{theme["tagPill"]};'
            f'font:600 16px {FONT_STACK};color:{theme["text"]}">'
            f'{badgeImg}<span>{escapeXml(presence.serverTagText)}</span></div>'
        )

    body = (
        f'<div xmlns="http://www.w3.org/1999/xhtml" '
        f'style="display:flex;align-items:center;gap:8px;font-family:{FONT_STACK}">'
        f'<div style="font:400 20px {FONT_STACK};color:{theme["subtext"]}">{handle}</div>'
        f'{pill}</div>'
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
