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
from ..helpers.activity import build_activity_row, build_activity_card
from ..helpers.avatar import build_avatar_circle
from ..helpers.pill import build_handle_pill_row, build_status_pill
from ..helpers.primitives import (
    build_text,
    fetch_data_uri,
    build_card_background,
    build_svg_root
)
from ..helpers.color import derive_panel

# Canvas
VIEWBOX_WIDTH = 700

# Spacing primitives
GAP_PILL_ACTIVITY = 8     # pill bottom -> activity panel top
CARD_BOTTOM_PAD   = 26    # last element bottom -> card bottom edge

LAYOUT = {
    "corner":      24,
    "banner_h":     192,
    "avatar_cx":    100,
    "avatar_cy":    174,
    "avatar_r":     84,
    "deco_scale":   1.18,
    "ring_width":   6,
    "pad":         28,

    "name_y":       308,
    "name_size":    40,

    "fo_box_y":      322,
    "fo_box_h":      40,

    "activity_art": 120,    # SINGLE source of truth — matches buildActivityRow default
    "activity_pad": 14,

    # custom status pill (floats beside avatar, independent of derive chain)
    "status_x":                225,   # ≈ avatar right edge, slight overlap like the screenshot
    "status_y":                190,   # ≈ avatar_cy - pill/2, sits at avatar's upper-middle
    "status_w":                450,   # hard truncation boundary for long statuses
    "status_h":                85,    # fits 2 wrapped lines: 2×~26 line-height + 2×14 pad ≈ 80, CJK + 5 = 85

    # left/top overflow room; right/bottom need none 
    # status_w/H are hard truncation bounds so content never reaches them.
    # NOTE: this also nudges the bubble up-left by 16px (foreignObject origin relocates content), 
    # which is intentional overlap, not a bug.
    "status_foreign_object_bleed": 16,

    # status-bubble tail dots (offsets are relative to status_x / status_y)
    "tail_big_radius":   24,   # large dot: hugs the bubble's top edge
    "tail_big_offset_x":  24,
    "tail_big_offset_y": -15,
    "tail_small_radius":   8,  # small dot: trails up toward the avatar
    "tail_small_offset_x": -8,
    "tail_small_offset_y": -40,
}


def _derive(layout: dict) -> dict:
    """
    Fill in dependent geometry derived from the spacing primitives.

    Mutates `layout` in place, adding the keys that downstream code reads so
    they are never hand-typed and can never drift from their inputs.

    Parameters
    ----------
    layout : dict
        The base layout mapping; extended in place with "pill_bottom",
        "activity_y", "activity_h", and "activity_bot".

    Returns
    -------
    dict
        The same `layout` mapping, for convenience.
    """

    layout["pill_bottom"]  = layout["fo_box_y"] + layout["fo_box_h"]
    layout["activity_y"]   = layout["pill_bottom"] + GAP_PILL_ACTIVITY
    layout["activity_h"]   = layout["activity_art"] + layout["activity_pad"] * 2
    layout["activity_bot"] = layout["activity_y"] + layout["activity_h"]

    return layout

_derive(LAYOUT)

# These values are now derived, not hardcoded anymore
VIEWBOX_HEIGHT_BASE     = LAYOUT["pill_bottom"]  + CARD_BOTTOM_PAD
VIEWBOX_HEIGHT_ACTIVITY = LAYOUT["activity_bot"] + CARD_BOTTOM_PAD


async def render_profile(
    presence: Presence,
    theme: Theme,
    http_client: httpx.AsyncClient,
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
    http_client : httpx.AsyncClient
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

    avatar_uri = await fetch_data_uri(presence.avatar_url, http_client)

    banner_uri = (
        await fetch_data_uri(presence.banner_url, http_client)
        if presence.banner_url else None
    )

    deco_uri = (
        await fetch_data_uri(presence.avatar_decoration_url, http_client)
        if presence.avatar_decoration_url else None
    )

    badge_uri = (
        await fetch_data_uri(presence.server_tag_badge_url, http_client)
        if presence.server_tag_badge_url else None
    )

    # card background fill (flat color OR gradient)
    card_defs, card_fill = build_card_background(theme, defs_id=f"cardBg-{uid}")

    if banner_uri:
        banner = (
            f'<defs><clipPath id="bannerClip-{uid}">'
            f'<rect x="0" y="0" width="{VIEWBOX_WIDTH}" height="{layout["banner_h"]}" '
            f'rx="{layout["corner"]}" /></clipPath></defs>'
            f'<image href="{banner_uri}" x="0" y="0" width="{VIEWBOX_WIDTH}" '
            f'height="{layout["banner_h"]}" preserveAspectRatio="xMidYMid slice" '
            f'clip-path="url(#bannerClip-{uid})" />'
        )

    else:
        fill = card_fill if theme.get("bg_gradient") else theme["tag_pill"]
        banner = (
            f'<rect x="0" y="0" width="{VIEWBOX_WIDTH}" height="{layout["banner_h"]}" '
            f'rx="{layout["corner"]}" fill="{fill}" />'
        )

    avatar = build_avatar_circle(
        avatar_uri=avatar_uri,
        cx=layout["avatar_cx"],
        cy=layout["avatar_cy"],
        radius=layout["avatar_r"],
        status=presence.status,
        bg_color=theme["background"],
        decoration_uri=deco_uri,
        decoration_scale=layout["deco_scale"],
        ring_width=layout["ring_width"],
        clip_id=f"avatarClip-{uid}",
    )

    name = build_text(
        x=layout["pad"], y=layout["name_y"],
        content=presence.display_name,
        fill=theme["text"],
        size=layout["name_size"],
        weight="700",
    )

    handle_and_pill = build_handle_pill_row(
        x=layout["pad"],
        y=layout["fo_box_y"],
        width=VIEWBOX_WIDTH - layout["pad"] * 2,
        height=layout["fo_box_h"],
        presence=presence,
        theme=theme,
        badge_uri=badge_uri,
    )

    status_pill = build_status_pill(
        presence.custom_status_text,
        presence.custom_status_emoji_unicode,
        presence.custom_status_emoji_url,
        theme,
        max_height=layout["status_h"],
    )

    foreign_object_bleed = layout["status_foreign_object_bleed"]

    status_foreign_object = (
        f'<foreignObject x="{layout["status_x"] - foreign_object_bleed}" '
        f'y="{layout["status_y"] - foreign_object_bleed}" '
        f'width="{layout["status_w"] + foreign_object_bleed}" '
        f'height="{layout["status_h"] + foreign_object_bleed}">{status_pill}</foreignObject>'
        if status_pill else ""
    )

    status_tail = ""
    if status_pill:
        build_dot = lambda center_x, center_y, radius: (
            f'<circle cx="{center_x}" cy="{center_y}" r="{radius}" fill="{theme["tag_pill"]}" />'
        )
        bubble_x, bubble_y = layout["status_x"], layout["status_y"]
        # big dot hugs bubble top edge; small dot trails up toward avatar
        status_tail = (
            build_dot(
                bubble_x + layout["tail_big_offset_x"],
                bubble_y + layout["tail_big_offset_y"],
                layout["tail_big_radius"],
            )
            + build_dot(
                bubble_x + layout["tail_small_offset_x"],
                bubble_y + layout["tail_small_offset_y"],
                layout["tail_small_radius"],
            )
        )

    activity_block = ""
    view_box_height = VIEWBOX_HEIGHT_BASE
    if presence.activity_name:
        large_uri = (
            await fetch_data_uri(presence.activity_large_image_url, http_client)
            if presence.activity_large_image_url else None
        )
        small_uri = (
            await fetch_data_uri(presence.activity_small_image_url, http_client)
            if presence.activity_small_image_url else None
        )

        panel_color = derive_panel(theme["background"])

        panel, inner_x, inner_y, _ = build_activity_card(
            x=layout["pad"],
            y=layout["activity_y"],
            width=VIEWBOX_WIDTH - layout["pad"] * 2,
            height=layout["activity_h"],
            fill=panel_color,
            padding=layout["activity_pad"],
        )

        row = build_activity_row(
            inner_x, inner_y, presence.activity_name,
            art=layout["activity_art"],
            text_color=theme["text"],
            sub_text_color=theme["subtext"],
            accent_color=theme["accent"],
            ring_color=panel_color,
            details=presence.activity_details,
            state=presence.activity_state,
            start=presence.activity_start,
            large_uri=large_uri,
            small_uri=small_uri,
            clip_id=f"activityArtClip-{uid}",
        )
        activity_block = panel + row
        view_box_height = VIEWBOX_HEIGHT_ACTIVITY

    height = int(width * view_box_height / VIEWBOX_WIDTH)

    return build_svg_root(
        width=width,
        height=height,
        view_box=f"0 0 {VIEWBOX_WIDTH} {view_box_height}",
        body=(
            f'{card_defs}'
            f'<rect width="{VIEWBOX_WIDTH}" height="{view_box_height}" rx="{layout["corner"]}" fill="{card_fill}" />'
            f'{banner}{avatar}{name}{handle_and_pill}{activity_block}{status_tail}{status_foreign_object}'
        ),
    )
