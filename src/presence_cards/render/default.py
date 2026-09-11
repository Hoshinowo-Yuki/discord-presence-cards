# SPDX-License-Identifier: MIT

import httpx

from presence_cards.store import Presence
from presence_cards.themes import Theme

from ..helpers.avatar import buildAvatarCircle
from ..helpers.pill import buildServerTagPill
from ..helpers.primitives import buildText, estimateTextWidth, fetchDataUri

CONTENT_LEFT = 120   # x where text/pill start, just right of the avatar
CARD_MIN_WIDTH = 340
CARD_HEIGHT = 120
RIGHT_PAD = 20


async def renderDefault(
    presence: Presence,
    theme: Theme,
    httpClient: httpx.AsyncClient,
    hideSpotify: bool = False,
) -> str:
    """Render the default presence card as an SVG string. Width grows to fit."""
    avatarUri = await fetchDataUri(presence.avatarUrl, httpClient)

    avatarMarkup = buildAvatarCircle(
        avatarUri=avatarUri,
        cx=60,
        cy=60,
        radius=36,
        status=presence.status,
        ringColor=theme["background"],
    )

    nameSize = 20
    nameWidth = estimateTextWidth(presence.displayName, nameSize)
    nameMarkup = buildText(
        x=CONTENT_LEFT, y=55, content=presence.displayName,
        fill=theme["text"], size=nameSize, weight="600",
    )
    rightEdge = CONTENT_LEFT + nameWidth

    tagMarkup = ""
    if presence.serverTagText:
        pillX = CONTENT_LEFT + nameWidth + 12
        badgeUri = None
        if presence.serverTagBadgeUrl:
            badgeUri = await fetchDataUri(presence.serverTagBadgeUrl, httpClient)

        tagMarkup, pillW = buildServerTagPill(
            x=pillX, cy=48,
            tagText=presence.serverTagText,
            badgeUri=badgeUri,
            textColor=theme["text"],
            pillColor=theme["tagPill"],
        )
        rightEdge = pillX + pillW

    activityMarkup = ""
    if presence.activityName and not hideSpotify:
        actSize = 14
        activityMarkup = buildText(
            x=CONTENT_LEFT, y=78, content=presence.activityName,
            fill=theme["subtext"], size=actSize,
        )
        rightEdge = max(rightEdge, CONTENT_LEFT + estimateTextWidth(presence.activityName, actSize))

    cardWidth = max(CARD_MIN_WIDTH, int(rightEdge) + RIGHT_PAD)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{cardWidth}" height="{CARD_HEIGHT}" viewBox="0 0 {cardWidth} {CARD_HEIGHT}">
  <rect width="{cardWidth}" height="{CARD_HEIGHT}" rx="12" fill="{theme["background"]}" />
  {avatarMarkup}
  {nameMarkup}
  {tagMarkup}
  {activityMarkup}
</svg>'''