# The MIT License (MIT)
#
# Copyright (c) 2026 Hoshino Yuki
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
# SPDX-License-Identifier: MIT

"""
Full profile card.

Banner, avatar, name, handle/tag row, optional
activity panel, and a floating custom-status bubble.

Layout geometry is derived from a handful of spacing
primitives rather than hand-typed.
"""

import secrets
import httpx
from ..store import Presence
from ..themes import Theme
from ..helpers.activity import buildActivityRow, buildActivityCard
from ..helpers.avatar import buildAvatarCircle
from ..helpers.pill import buildHandlePillRow, buildStatusPill
from ..helpers.primitives import (
    buildText,
    fetchDataUri,
    buildCardBackground,
    buildSvgRoot
)
from ..helpers.color import derivePanel

# Canvas
VIEWBOX_WIDTH = 700

# Spacing primitives
GAP_PILL_ACTIVITY = 8     # pill bottom -> activity panel top
CARD_BOTTOM_PAD   = 26    # last element bottom -> card bottom edge

LAYOUT = {
    "corner":      24,
    "bannerH":     192,
    "avatarCx":    100,
    "avatarCy":    174,
    "avatarR":     84,
    "decoScale":   1.18,
    "ringWidth":   6,
    "pad":         28,

    "nameY":       308,
    "nameSize":    40,

    "foBoxY":      322,
    "foBoxH":      40,

    "activityArt": 120,    # SINGLE source of truth — matches buildActivityRow default
    "activityPad": 14,

    # custom status pill (floats beside avatar, independent of derive chain)
    "statusX":                225,   # ≈ avatar right edge, slight overlap like the screenshot
    "statusY":                190,   # ≈ avatarCy - pill/2, sits at avatar's upper-middle
    "statusW":                450,   # hard truncation boundary for long statuses
    "statusH":                85,    # fits 2 wrapped lines: 2×~26 line-height + 2×14 pad ≈ 80, CJK + 5 = 85
    "statusForeignObjectBleed": 16,  # foreignObject overflow allowance around the bubble (left/top origin + w/h)

    # status-bubble tail dots (offsets are relative to statusX / statusY)
    "tailBigRadius":   24,   # large dot: hugs the bubble's top edge
    "tailBigOffsetX":  24,
    "tailBigOffsetY": -15,
    "tailSmallRadius":   8,  # small dot: trails up toward the avatar
    "tailSmallOffsetX": -8,
    "tailSmallOffsetY": -40,
}


def _derive(layout: dict) -> dict:
    """
    Fill in dependent geometry derived from the spacing primitives.

    Mutates `layout` in place, adding the keys that downstream code reads so
    they are never hand-typed and can never drift from their inputs.

    Parameters
    ----------
    layout : dict
        The base layout mapping; extended in place with "pillBottom",
        "activityY", "activityH", and "activityBot".

    Returns
    -------
    dict
        The same `layout` mapping, for convenience.
    """

    layout["pillBottom"]  = layout["foBoxY"] + layout["foBoxH"]
    layout["activityY"]   = layout["pillBottom"] + GAP_PILL_ACTIVITY
    layout["activityH"]   = layout["activityArt"] + layout["activityPad"] * 2
    layout["activityBot"] = layout["activityY"] + layout["activityH"]

    return layout

_derive(LAYOUT)

VIEWBOX_HEIGHT_BASE     = LAYOUT["pillBottom"]  + CARD_BOTTOM_PAD   # = 386
VIEWBOX_HEIGHT_ACTIVITY = LAYOUT["activityBot"] + CARD_BOTTOM_PAD   # = 494


async def renderProfile(
    presence: Presence,
    theme: Theme,
    httpClient: httpx.AsyncClient,
    width: int = 500,
) -> str:
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Render the full profile card as an SVG string.

    Composes the banner, ringed avatar (with optional decoration), display
    name, handle/tag row, an optional activity panel, and a floating
    custom-status bubble.
    
    The viewBox height switches between a base and a taller value
    depending on whether an activity panel is present; the output
    width is the caller's `width`, with height scaled to preserve
    the aspect ratio.

    All internal SVG element ids are suffixed with a per-render token so
    that multiple cards embedded in a single document keep isolated id
    namespaces and never cross-clip one another.

    Parameters
    ----------
    presence : Presence
        The presence record to render.
    theme : Theme
        The resolved theme supplying colors and any background gradient.
    httpClient : httpx.AsyncClient
        The async client used to inline the avatar, banner, decoration,
        badge, and activity images.
    width : int, optional
        The output width in pixels; height is derived from it to preserve
        the viewBox aspect ratio (default is 500).

    Returns
    -------
    str
        The complete SVG document for the card.
    """
    layout = LAYOUT

    # Per-render id namespace. Suffix (not prefix) so ids never start with a
    # digit — XML ids must begin with a letter/underscore.
    uid = secrets.token_hex(4)

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

    # card background fill (flat color OR gradient)
    cardDefs, cardFill = buildCardBackground(theme, defsId=f"cardBg-{uid}")

    if bannerUri:
        banner = (
            f'<defs><clipPath id="bannerClip-{uid}">'
            f'<rect x="0" y="0" width="{VIEWBOX_WIDTH}" height="{layout["bannerH"]}" '
            f'rx="{layout["corner"]}" /></clipPath></defs>'
            f'<image href="{bannerUri}" x="0" y="0" width="{VIEWBOX_WIDTH}" '
            f'height="{layout["bannerH"]}" preserveAspectRatio="xMidYMid slice" '
            f'clip-path="url(#bannerClip-{uid})" />'
        )

    else:
        fill = cardFill if theme.get("bgGradient") else theme["tagPill"]
        banner = (
            f'<rect x="0" y="0" width="{VIEWBOX_WIDTH}" height="{layout["bannerH"]}" '
            f'rx="{layout["corner"]}" fill="{fill}" />'
        )

    avatar = buildAvatarCircle(
        avatarUri=avatarUri,
        cx=layout["avatarCx"], cy=layout["avatarCy"], radius=layout["avatarR"],
        status=presence.status,
        backgroundColor=theme["background"],
        decoUri=decoUri, decoScale=layout["decoScale"],
        ringWidth=layout["ringWidth"],
        clipId=f"avatarClip-{uid}",
    )

    name = buildText(
        x=layout["pad"], y=layout["nameY"], content=presence.displayName,
        fill=theme["text"], size=layout["nameSize"], weight="700",
    )

    handleAndPill = buildHandlePillRow(
        x=layout["pad"], y=layout["foBoxY"],
        width=VIEWBOX_WIDTH - layout["pad"] * 2, height=layout["foBoxH"],
        presence=presence, theme=theme, badgeUri=badgeUri,
    )

    statusPill = buildStatusPill(
        presence.customStatusText,
        presence.customStatusEmojiUnicode,
        presence.customStatusEmojiUrl,
        theme,
        maxHeight=layout["statusH"],
    )

    foreignObjectBleed = layout["statusForeignObjectBleed"]

    statusForeignObject = (
        f'<foreignObject x="{layout["statusX"] - foreignObjectBleed}" '
        f'y="{layout["statusY"] - foreignObjectBleed}" '
        f'width="{layout["statusW"] + foreignObjectBleed}" '
        f'height="{layout["statusH"] + foreignObjectBleed}">{statusPill}</foreignObject>'
        if statusPill else ""
    )

    statusTail = ""
    if statusPill:
        buildDot = lambda centerX, centerY, radius: (
            f'<circle cx="{centerX}" cy="{centerY}" r="{radius}" fill="{theme["tagPill"]}" />'
        )
        bubbleX, bubbleY = layout["statusX"], layout["statusY"]
        # big dot hugs bubble top edge; small dot trails up toward avatar
        statusTail = (
            buildDot(
                bubbleX + layout["tailBigOffsetX"],
                bubbleY + layout["tailBigOffsetY"],
                layout["tailBigRadius"],
            )
            + buildDot(
                bubbleX + layout["tailSmallOffsetX"],
                bubbleY + layout["tailSmallOffsetY"],
                layout["tailSmallRadius"],
            )
        )

    activityBlock = ""
    viewBoxHeight = VIEWBOX_HEIGHT_BASE
    if presence.activityName:
        largeUri = (
            await fetchDataUri(presence.activityLargeImageUrl, httpClient)
            if presence.activityLargeImageUrl else None
        )
        smallUri = (
            await fetchDataUri(presence.activitySmallImageUrl, httpClient)
            if presence.activitySmallImageUrl else None
        )

        panelColor = derivePanel(theme["background"])

        panel, innerX, innerY, _ = buildActivityCard(
            x=layout["pad"], y=layout["activityY"],
            width=VIEWBOX_WIDTH - layout["pad"] * 2, height=layout["activityH"],
            fill=panelColor, padding=layout["activityPad"],
        )

        row = buildActivityRow(
            innerX, innerY, presence.activityName,
            art=layout["activityArt"],
            textColor=theme["text"],
            subTextColor=theme["subtext"],
            accentColor=theme["accent"],
            ringColor=panelColor,
            details=presence.activityDetails,
            start=presence.activityStart,
            largeUri=largeUri, smallUri=smallUri,
            clipId=f"activityArtClip-{uid}",
        )
        activityBlock = panel + row
        viewBoxHeight = VIEWBOX_HEIGHT_ACTIVITY

    height = int(width * viewBoxHeight / VIEWBOX_WIDTH)

    return buildSvgRoot(
        width=width,
        height=height,
        viewBox=f"0 0 {VIEWBOX_WIDTH} {viewBoxHeight}",
        body=(
            f'{cardDefs}'
            f'<rect width="{VIEWBOX_WIDTH}" height="{viewBoxHeight}" rx="{layout["corner"]}" fill="{cardFill}" />'
            f'{banner}{avatar}{name}{handleAndPill}{activityBlock}{statusTail}{statusForeignObject}'
        ),
    )