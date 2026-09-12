# SPDX-License-Identifier: MIT

import httpx

from ..store import Presence
from ..themes import Theme

from ..helpers.activity import buildActivityRow, buildActivityCard
from ..helpers.avatar import buildAvatarCircle
from ..helpers.pill import buildHandlePillRow, buildStatusPill
from ..helpers.primitives import buildText, fetchDataUri, buildCardBackground, buildSvgRoot
from ..helpers.color import derivePanel

# ── canvas ─────────────────────────────────────────────────────────
VB_W = 700

# ── spacing primitives (tune these; everything downstream derives) ──
GAP_PILL_ACTIVITY = 8     # pill bottom → activity panel top
CARD_BOTTOM_PAD   = 26    # last element bottom → card bottom edge

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

# ── custom status pill (floats beside avatar, independent of derive chain) ──
    "statusX":     225,   # ≈ avatar right edge, slight overlap like the screenshot
    "statusY":     190,   # ≈ avatarCy - pill/2, sits at avatar's upper-middle
    "statusW":     450,   # hard truncation boundary for long statuses
    "statusH":     85,    # fits 2 wrapped lines: 2×~26 line-height + 2×14 pad ≈ 80, CJK + 5 = 85
}


def _derive(L: dict) -> dict:
    """Dependent geometry — never hand-typed."""
    L["pillBottom"]  = L["foBoxY"] + L["foBoxH"]
    L["activityY"]   = L["pillBottom"] + GAP_PILL_ACTIVITY
    L["activityH"]   = L["activityArt"] + L["activityPad"] * 2
    L["activityBot"] = L["activityY"] + L["activityH"]
    return L


_derive(LAYOUT)

VB_H_BASE     = LAYOUT["pillBottom"]  + CARD_BOTTOM_PAD   # = 386
VB_H_ACTIVITY = LAYOUT["activityBot"] + CARD_BOTTOM_PAD   # = 494


async def renderProfile(
    presence: Presence,
    theme: Theme,
    httpClient: httpx.AsyncClient,
    width: int = 500,
) -> str:
    """Render the full profile card (banner + avatar + name + tag + activity)."""
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

    # ── card background fill (flat color OR gradient) ──────────────
    cardDefs, cardFill = buildCardBackground(theme, defsId="profCardBg")

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
        fill = cardFill if theme.get("bgGradient") else theme["tagPill"]
        banner = (
            f'<rect x="0" y="0" width="{VB_W}" height="{L["bannerH"]}" '
            f'rx="{L["corner"]}" fill="{fill}" />'
        )

    avatar = buildAvatarCircle(
        avatarUri=avatarUri,
        cx=L["avatarCx"], cy=L["avatarCy"], radius=L["avatarR"],
        status=presence.status,
        ringColor=theme["background"],
        decoUri=decoUri, decoScale=L["decoScale"],
        ringWidth=L["ringWidth"],
        clipId="profAvatarClip",
    )

    name = buildText(
        x=L["pad"], y=L["nameY"], content=presence.displayName,
        fill=theme["text"], size=L["nameSize"], weight="700",
    )
    handleAndPill = buildHandlePillRow(
        x=L["pad"], y=L["foBoxY"],
        width=VB_W - L["pad"] * 2, height=L["foBoxH"],
        presence=presence, theme=theme, badgeUri=badgeUri,
    )

    statusPill = buildStatusPill(
            presence.customStatusText,
            presence.customStatusEmojiUnicode,
            presence.customStatusEmojiUrl,
            theme,
            maxHeight=L["statusH"],
        )

    statusFo = (
        f'<foreignObject x="{L["statusX"] - 16}" y="{L["statusY"] - 16}" '
        f'width="{L["statusW"] + 16}" height="{L["statusH"] + 16}">{statusPill}</foreignObject>'
        if statusPill else ""
    )

    statusTail = ""
    if statusPill:
        dot = lambda cx, cy, r: (
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{theme["tagPill"]}" />'
        )
        bx, by = L["statusX"], L["statusY"]
        # big dot hugs bubble top edge; small dot trails up toward avatar
        statusTail = dot(bx + 24, by - 15, 24) + dot(bx - 8, by - 40, 8)

    activityBlock = ""
    vbH = VB_H_BASE
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
            x=L["pad"], y=L["activityY"],
            width=VB_W - L["pad"] * 2, height=L["activityH"],
            fill=panelColor, padding=L["activityPad"],
        )
        row = buildActivityRow(
            innerX, innerY, presence.activityName,
            art=L["activityArt"],
            textColor=theme["text"],
            subTextColor=theme["subtext"],
            accentColor=theme["accent"],
            ringColor=panelColor,
            details=presence.activityDetails,
            start=presence.activityStart,
            largeUri=largeUri, smallUri=smallUri,
        )
        activityBlock = panel + row
        vbH = VB_H_ACTIVITY

    height = int(width * vbH / VB_W)

    return buildSvgRoot(
        width=width,
        height=height,
        viewBox=f"0 0 {VB_W} {vbH}",
        body=(
            f'{cardDefs}'
            f'<rect width="{VB_W}" height="{vbH}" rx="{L["corner"]}" fill="{cardFill}" />'
            f'{banner}{avatar}{name}{handleAndPill}{activityBlock}{statusTail}{statusFo}'
        ),
    )