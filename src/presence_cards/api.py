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
from .render import renderDefault, renderProfile
from .helpers.enrich import enrichPresence
from .helpers.responses import notFoundCard, svgResponse
from .helpers.theme_resolver import resolveThemeParam

router = APIRouter()


@router.get("/profile/{userId}")
async def profileCard(
    userId: int,
    request: Request,
    theme: str = Query("dark"),
    color: Optional[str] = Query(None),
    width: int = Query(500),
):
    presence = store.getPresence(userId)
    if presence is None:
        return notFoundCard()

    await enrichPresence(presence, userId)

    try:
        resolved = resolveThemeParam(
            theme=theme, color=color, accentColor=presence.accentColor
        )
    except ValueError:
        return Response("bad color param", status_code=400)

    svg = await renderProfile(
        presence, resolved, request.app.state.httpClient, width=width
    )
    return svgResponse(svg)


@router.get("/presence/{userId}")
async def presenceCard(
    userId: int,
    request: Request,
    theme: str = Query("dark"),
    color: Optional[str] = Query(None),
    hideSpotify: bool = Query(False),
):
    presence = store.getPresence(userId)
    if presence is None:
        return notFoundCard()

    try:
        resolvedTheme = resolveThemeParam(theme=theme, color=color, accentColor=None)
    except ValueError:
        return Response("bad color param", status_code=400)

    svg = await renderDefault(
        presence, resolvedTheme, request.app.state.httpClient, hideSpotify=hideSpotify
    )
    return svgResponse(svg)
