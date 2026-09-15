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
Default presence card.

A compact horizontal row that grows to fit.
"""

import secrets
import httpx
from ..store import Presence
from ..themes import Theme
from ..helpers.avatar import build_avatar_circle
from ..helpers.pill import build_server_tag_pill
from ..helpers.primitives import (
    build_text,
    estimate_text_width,
    fetch_data_uri,
    build_card_background,
    build_svg_root,
)

CONTENT_LEFT = 120   # x where text/pill start, just right of the avatar
CARD_MIN_WIDTH = 340
CARD_HEIGHT = 120
RIGHT_PAD = 20


async def render_default(
    presence: Presence,
    theme: Theme,
    http_client: httpx.AsyncClient,
    hide_spotify: bool = False,
) -> str:
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Render the default presence card as an SVG string.

    The card is a compact horizontal row (avatar, name, optional server-tag
    pill, optional activity line) whose width grows to fit its content down
    to a minimum of `CARD_MIN_WIDTH`.

    All internal SVG element ids are suffixed with a per-render token so
    that multiple cards embedded in a single document keep isolated id
    namespaces and never cross-clip one another.

    Parameters
    ----------
    presence : Presence
        The presence record to render.
    theme : Theme
        The resolved theme supplying colors and any background gradient.
    http_client : httpx.AsyncClient
        The async client used to inline the avatar and badge images.
    hide_spotify : bool, optional
        When True, the activity line is suppressed (default is False).

    Returns
    -------
    str
        The complete SVG document for the card.
    """

    # Per-render id namespace. Suffix (not prefix) so ids never start with a
    # digit — XML ids must begin with a letter/underscore.
    uid = secrets.token_hex(4)

    avatar_uri = await fetch_data_uri(presence.avatar_url, http_client)

    card_defs, card_fill = build_card_background(theme, defs_id=f"cardBg-{uid}")

    avatar_markup = build_avatar_circle(
        avatar_uri=avatar_uri,
        cx=60,
        cy=60,
        radius=36,
        status=presence.status,
        bg_color=theme["background"],
        clip_id=f"avatarClip-{uid}",
    )

    name_size = 20
    name_width = estimate_text_width(presence.display_name, name_size)
    name_markup = build_text(
        x=CONTENT_LEFT, y=55, content=presence.display_name,
        fill=theme["text"], size=name_size, weight="600",
    )
    right_edge = CONTENT_LEFT + name_width

    tag_markup = ""
    if presence.server_tag_text:
        pill_x = CONTENT_LEFT + name_width + 12
        badge_uri = None
        if presence.server_tag_badge_url:
            badge_uri = await fetch_data_uri(presence.server_tag_badge_url, http_client)

        tag_markup, pill_width = build_server_tag_pill(
            x=pill_x,
            cy=48,
            tag_text=presence.server_tag_text,
            badge_uri=badge_uri,
            text_color=theme["text"],
            pill_color=theme["tag_pill"],
        )
        right_edge = pill_x + pill_width

    activity_markup = ""
    if presence.activity_name and not hide_spotify:
        activity_size = 14
        activity_markup = build_text(
            x=CONTENT_LEFT,
            y=78,
            content=presence.activity_name,
            fill=theme["subtext"],
            size=activity_size,
        )
        right_edge = max(
            right_edge,
            CONTENT_LEFT + estimate_text_width(presence.activity_name, activity_size),
        )

    card_width = max(CARD_MIN_WIDTH, int(right_edge) + RIGHT_PAD)

    return build_svg_root(
        width=card_width,
        height=CARD_HEIGHT,
        view_box=f"0 0 {card_width} {CARD_HEIGHT}",
        body=(
            f'{card_defs}'
            f'<rect width="{card_width}" height="{CARD_HEIGHT}" rx="12" fill="{card_fill}" />'
            f'{avatar_markup}{name_markup}{tag_markup}{activity_markup}'
        ),
    )
