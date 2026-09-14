# SPDX-License-Identifier: MIT
"""Default presence card: a compact horizontal row that grows to fit."""

import httpx
from ..store import Presence
from ..themes import Theme
from ..helpers.avatar import buildAvatarCircle
from ..helpers.pill import buildServerTagPill
from ..helpers.primitives import (
    buildText,
    estimateTextWidth,
    fetchDataUri,
    buildCardBackground,
    buildSvgRoot,
)

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
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Render the default presence card as an SVG string.

    The card is a compact horizontal row (avatar, name, optional server-tag
    pill, optional activity line) whose width grows to fit its content down
    to a minimum of `CARD_MIN_WIDTH`.

    Parameters
    ----------
    presence : Presence
        The presence record to render.
    theme : Theme
        The resolved theme supplying colors and any background gradient.
    httpClient : httpx.AsyncClient
        The async client used to inline the avatar and badge images.
    hideSpotify : bool, optional
        When True, the activity line is suppressed (default is False).

    Returns
    -------
    str
        The complete SVG document for the card.
    """

    avatarUri = await fetchDataUri(presence.avatarUrl, httpClient)

    cardDefs, cardFill = buildCardBackground(theme)

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

        tagMarkup, pillWidth = buildServerTagPill(
            x=pillX, cy=48,
            tagText=presence.serverTagText,
            badgeUri=badgeUri,
            textColor=theme["text"],
            pillColor=theme["tagPill"],
        )
        rightEdge = pillX + pillWidth

    activityMarkup = ""
    if presence.activityName and not hideSpotify:
        activitySize = 14
        activityMarkup = buildText(
            x=CONTENT_LEFT, y=78, content=presence.activityName,
            fill=theme["subtext"], size=activitySize,
        )
        rightEdge = max(
            rightEdge,
            CONTENT_LEFT + estimateTextWidth(presence.activityName, activitySize),
        )

    cardWidth = max(CARD_MIN_WIDTH, int(rightEdge) + RIGHT_PAD)

    return buildSvgRoot(
        width=cardWidth,
        height=CARD_HEIGHT,
        viewBox=f"0 0 {cardWidth} {CARD_HEIGHT}",
        body=(
            f'{cardDefs}'
            f'<rect width="{cardWidth}" height="{CARD_HEIGHT}" rx="12" fill="{cardFill}" />'
            f'{avatarMarkup}{nameMarkup}{tagMarkup}{activityMarkup}'
        ),
    )
