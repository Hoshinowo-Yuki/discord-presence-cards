# SPDX-License-Identifier: MIT

import asyncio
import os
from contextlib import asynccontextmanager
import discord
import httpx
from fastapi import FastAPI, Query, Response

from .bot import bot
from .render import renderDefault, renderProfile
from .store import store
from .themes import resolveTheme

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
async def profileCard(userId: int, theme: str = Query("dark"), width: int = Query(500)):
    presence = store.getPresence(userId)
    if presence is None:
        return Response(
            content="<svg xmlns='http://www.w3.org/2000/svg' width='340' height='120'>"
            "<rect width='340' height='120' rx='12' fill='#2f3136'/>"
            "<text x='24' y='64' fill='#b9bbbe' font-family='sans-serif' font-size='16'>"
            "Presence not found</text></svg>",
            media_type="image/svg+xml",
            status_code=404,
        )

    # banner is NOT on the gateway — fetch via REST (consider caching this!)
    try:
        user = await bot.fetch_user(userId)
        if user.banner:
            presence.bannerUrl = str(user.banner.replace(format="gif", size=1024).url)
    except discord.HTTPError:
        pass  # renderProfile falls back to flat banner strip

    svg = await renderProfile(presence, resolveTheme(theme),
                              app.state.httpClient, width=width)
    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "no-cache"})


@app.get("/presence/{userId}")
async def presenceCard(
    userId: int,
    theme: str = Query("dark"),
    hideSpotify: bool = Query(False),
):
    presence = store.getPresence(userId)
    if presence is None:
        return Response(
            content="<svg xmlns='http://www.w3.org/2000/svg' width='340' height='120'>"
            "<rect width='340' height='120' rx='12' fill='#2f3136'/>"
            "<text x='24' y='64' fill='#b9bbbe' font-family='sans-serif' font-size='16'>"
            "Presence not found</text></svg>",
            media_type="image/svg+xml",
            status_code=404,
        )

    resolvedTheme = resolveTheme(theme)
    svg = await renderDefault(
        presence,
        resolvedTheme,
        app.state.httpClient,
        hideSpotify=hideSpotify,
    )
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "no-cache"},
    )