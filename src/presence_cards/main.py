# SPDX-License-Identifier: MIT

import asyncio
import os
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Query, Response

from .bot import bot
from .render import renderDefault, renderProfile
from .store import store

from .helpers.enrich import enrichPresence
from .helpers.responses import notFoundCard, svgResponse
from .helpers.theme_resolver import resolveThemeParam
from .themes import resolveTheme
from typing import Optional

TOKEN = os.environ["DISCORD_TOKEN"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.httpClient = httpx.AsyncClient()
    botTask = asyncio.create_task(bot.start(TOKEN))
    try:
        yield
    finally:
        await bot.close()
        await app.state.httpClient.aclose()
        botTask.cancel()


app = FastAPI(lifespan=lifespan)

@app.get("/profile/{userId}")
async def profileCard(userId: int, theme: str = Query("dark"),
                      color: Optional[str] = Query(None), width: int = Query(500)):
    presence = store.getPresence(userId)
    if presence is None:
        return notFoundCard()

    await enrichPresence(presence, userId)

    try:
        resolved = resolveThemeParam(theme=theme, color=color,
                                     accentColor=presence.accentColor)
    except ValueError:
        return Response("bad color param", status_code=400)

    svg = await renderProfile(presence, resolved, app.state.httpClient, width=width)
    return svgResponse(svg)


@app.get("/presence/{userId}")
async def presenceCard(
    userId: int,
    theme: str = Query("dark"),
    color: Optional[str] = Query(None),
    hideSpotify: bool = Query(False),
):
    presence = store.getPresence(userId)
    if presence is None:
        return notFoundCard()

    try:
        resolvedTheme = resolveThemeParam(
            theme=theme,
            color=color,
            accentColor=None,      # ← see note
        )
    except ValueError:
        return Response("bad color param", status_code=400)

    svg = await renderDefault(
        presence, resolvedTheme, app.state.httpClient,
        hideSpotify=hideSpotify,
    )
    return svgResponse(svg)