# SPDX-License-Identifier: MIT

import httpx

from presence_cards.store import Presence
from presence_cards.themes import Theme

from ..helpers.avatar import buildAvatarCircle
from ..helpers.pill import buildHandlePillRow
from ..helpers.primitives import buildText, fetchDataUri

# 700x370 internal canvas is FIXED. Only outer `width` is user-adjustable.
VB_W, VB_H = 700, 370

LAYOUT = {
    "corner":     24,
    "bannerH":    175,
    "avatarCx":   100,
    "avatarCy":   174,
    "avatarR":    84,
    "decoScale":  1.18,
    "ringWidth":  6,
    "pad":        28,
    "nameY":      304,
    "nameSize":   40,
    "foBoxY":     322,
    "foBoxH":     56,
}


async def renderProfile(
    presence: Presence,
    theme: Theme,
    httpClient: httpx.AsyncClient,
    width: int = 500,
) -> str:
    """Render the full profile card (banner + decorated avatar + name + tag)."""
    L = LAYOUT

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

    avatar = buildAvatarCircle(
        avatarUri=avatarUri,
        cx=L["avatarCx"],
        cy=L["avatarCy"],
        radius=L["avatarR"],
        status=presence.status,
        ringColor=theme["background"],
        decoUri=decoUri,
        decoScale=L["decoScale"],
        ringWidth=L["ringWidth"],
        clipId="profAvatarClip",
    )

    name = buildText(
        x=L["pad"], y=L["nameY"], content=presence.displayName,
        fill=theme["text"], size=L["nameSize"], weight="700",
    )

    handleAndPill = buildHandlePillRow(
        x=L["pad"],
        y=L["foBoxY"],
        width=VB_W - L["pad"] * 2,
        height=L["foBoxH"],
        presence=presence,
        theme=theme,
        badgeUri=badgeUri,
    )

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