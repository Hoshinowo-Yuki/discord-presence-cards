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

def buildStatusPill(
    text: Optional[str],
    emojiUnicode: Optional[str],
    emojiUrl: Optional[str],
    theme: dict,
    emojiSize: int = 26,
) -> str:
    """Custom-status bubble: [emoji] italic text. Emoji is either a custom
    CDN asset (<img>) or a unicode codepoint (<span>, font-rendered)."""
    if not (text or emojiUnicode or emojiUrl):
        return ""

    if emojiUrl:
        emojiEl = (
            f'<img src="{emojiUrl}" width="{emojiSize}" height="{emojiSize}" '
            f'style="display:block" />'
        )
    elif emojiUnicode:
        emojiEl = (
            f'<span style="font-family:{FONT_STACK};'
            f'font-size:{emojiSize}px">{escapeXml(emojiUnicode)}</span>'
        )
    else:
        emojiEl = ""

    textEl = (
        f'<span style="font:italic 400 20px {FONT_STACK};'
        f'color:{theme["subtext"]};overflow:hidden;text-overflow:ellipsis;'
        f'white-space:nowrap">{escapeXml(text)}</span>'
        if text else ""
    )

    return (
        f'<div xmlns="http://www.w3.org/1999/xhtml" '   # ← this was missing
        f'style="display:inline-flex;align-items:center;gap:9px;'
        f'padding:12px 24px;border-radius:14px;background:{theme["tagPill"]};'
        f'max-width:100%;overflow:hidden">'
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
            f'padding:4px 14px 4px 11px;border-radius:13px;background:{theme["tagPill"]};'
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
