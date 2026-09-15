"""
The MIT License (MIT)

Copyright (c) 2026 Hoshino Yuki

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

# SPDX-License-Identifier: MIT

from typing import Optional

from fastapi import APIRouter, Query, Request, Response

from .store import store
from .render import render_default, render_profile
from .helpers.enrich import enrich_presence
from .helpers.responses import not_found_card, svg_response
from .helpers.theme_resolver import resolve_theme_param

router = APIRouter()


@router.get("/profile/{user_id}")
async def profile_card(
    user_id: int,
    request: Request,
    theme: str = Query("dark"),
    color: Optional[str] = Query(None),
    width: int = Query(500),
):
    presence = store.get_presence(user_id)
    if presence is None:
        return not_found_card()

    await enrich_presence(presence, user_id)

    try:
        resolved = resolve_theme_param(
            theme=theme, color=color, accent_color=presence.accent_color
        )
    except ValueError:
        return Response("bad color param", status_code=400)

    svg = await render_profile(
        presence, resolved, request.app.state.http_client, width=width
    )
    return svg_response(svg)


@router.get("/presence/{user_id}")
async def presence_card(
    user_id: int,
    request: Request,
    theme: str = Query("dark"),
    color: Optional[str] = Query(None),
    hide_spotify: bool = Query(False, alias="hideSpotify"),
):
    presence = store.get_presence(user_id)
    if presence is None:
        return not_found_card()

    try:
        resolved_theme = resolve_theme_param(theme=theme, color=color, accent_color=None)
    except ValueError:
        return Response("bad color param", status_code=400)

    svg = await render_default(
        presence, resolved_theme, request.app.state.http_client, hide_spotify=hide_spotify
    )
    return svg_response(svg)
