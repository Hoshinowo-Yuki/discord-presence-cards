# SPDX-License-Identifier: MIT

import httpx

from presence_cards.store import Presence
from svgHelpers import fetchDataUri, buildText, escapeXml, FONT_STACK
from presence_cards.themes import Theme, resolveStatusColor

# 700x370 internal canvas is FIXED. Only outer `width` is user-adjustable.
VB_W, VB_H = 700, 370

LAYOUT = {
    "corner":     24,
    "bannerH":    175,   # was 150 — banner bottom now meets avatar center
    "avatarCx":   100,
    "avatarCy":   174,   # was 170 — sits ON the banner edge, big overlap
    "avatarR":    84,    # was 56 — larger, matches the showcase proportions
    "decoScale":  1.18,
    "pad":        28,    # left padding for the stacked text column
    "nameY":      304,   # baseline of display name (below avatar bottom ~258)
    "nameSize":   40,
    "foBoxY":     322,   # handle + pill row, stacked under the name
    "foBoxH":     56,
}


def _buildAvatarWithDecoration(avatarUri, decoUri, statusColor, ringColor) -> str:
    L = LAYOUT
    cx, cy, r = L["avatarCx"], L["avatarCy"], L["avatarR"]
    size = r * 2
    x, y = cx - r, cy - r

    parts = [
        f'<defs><clipPath id="profAvatarClip">'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" /></clipPath></defs>',
        # ring behind avatar (separates it from banner)
        f'<circle cx="{cx}" cy="{cy}" r="{r + 6}" fill="{ringColor}" />',
        f'<image href="{avatarUri}" x="{x}" y="{y}" width="{size}" height="{size}" '
        f'clip-path="url(#profAvatarClip)" />',
    ]

    if decoUri:
        dSize = int(size * L["decoScale"])
        dx = cx - dSize // 2
        dy = cy - dSize // 2
        parts.append(
            f'<image href="{decoUri}" x="{dx}" y="{dy}" '
            f'width="{dSize}" height="{dSize}" />'
        )

    # status dot, lower-right
    dotCx = cx + int(r * 0.72)
    dotCy = cy + int(r * 0.72)
    dotR = max(7, int(r * 0.2))
    parts.append(f'<circle cx="{dotCx}" cy="{dotCy}" r="{dotR + 4}" fill="{ringColor}" />')
    parts.append(f'<circle cx="{dotCx}" cy="{dotCy}" r="{dotR}" fill="{statusColor}" />')

    return "".join(parts)


def _buildHandleAndPill(presence: Presence, theme: Theme, badgeUri) -> str:
    """XHTML inside <foreignObject>: @handle with [badge] TAG pill inline after it."""
    L = LAYOUT
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
            f'font:600 16px {FONT_STACK};color:{theme["text"]}">'   # margin-top removed
            f'{badgeImg}<span>{escapeXml(presence.serverTagText)}</span></div>'
        )

    body = (
        f'<div xmlns="http://www.w3.org/1999/xhtml" '
        f'style="display:flex;align-items:center;gap:8px;font-family:{FONT_STACK}">'  # flex row
        f'<div style="font:400 20px {FONT_STACK};color:{theme["subtext"]}">{handle}</div>'
        f'{pill}</div>'
    )

    return (
        f'<foreignObject x="{L["pad"]}" y="{L["foBoxY"]}" '
        f'width="{VB_W - L["pad"] * 2}" height="{L["foBoxH"]}">'
        f'{body}</foreignObject>'
    )

async def renderProfile(
    presence: Presence,
    theme: Theme,
    httpClient: httpx.AsyncClient,
    width: int = 500,
) -> str:
    """Render the full profile card (banner + decorated avatar + name + tag)."""
    L = LAYOUT
    statusColor = resolveStatusColor(presence.status)

    avatarUri = await fetchDataUri(presence.avatarUrl, httpClient)
    bannerUri = (
        await fetchDataUri(presence.bannerUrl, httpClient)
        if presence.bannerUrl else None
    )
    decoUri = (
        await fetchDataUri(presence.avatarDecorationUrl, httpClient)
        if presence.avatarDecorationUrl else None
    )
    badgeUri = (
        await fetchDataUri(presence.serverTagBadgeUrl, httpClient)
        if presence.serverTagBadgeUrl else None
    )

    # banner (or flat fill) clipped to the card's top, respecting rounding
    if bannerUri:
        banner = (
            f'<defs><clipPath id="bannerClip">'
            f'<rect x="0" y="0" width="{VB_W}" height="{L["bannerH"]}" '
            f'rx="{L["corner"]}" /></clipPath></defs>'
            f'<image href="{bannerUri}" x="0" y="0" width="{VB_W}" '
            f'height="{L["bannerH"]}" preserveAspectRatio="xMidYMid slice" '
            f'clip-path="url(#bannerClip)" />'
        )
    else:
        banner = (
            f'<rect x="0" y="0" width="{VB_W}" height="{L["bannerH"]}" '
            f'rx="{L["corner"]}" fill="{theme["tagPill"]}" />'
        )

    avatar = _buildAvatarWithDecoration(
        avatarUri, decoUri, statusColor, theme["background"]
    )

    name = buildText(
        x=L["pad"], y=L["nameY"], content=presence.displayName,
        fill=theme["text"], size=L["nameSize"], weight="700",
    )


    handleAndPill = _buildHandleAndPill(presence, theme, badgeUri)

    # outer width scales; internal coords stay in the 700x370 viewBox
    height = int(width * VB_H / VB_W)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {VB_W} {VB_H}">'
        f'<rect width="{VB_W}" height="{VB_H}" rx="{L["corner"]}" '
        f'fill="{theme["background"]}" />'
        f'{banner}{avatar}{name}{handleAndPill}'
        f'</svg>'
    )