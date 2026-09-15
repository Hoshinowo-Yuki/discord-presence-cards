# SPDX-License-Identifier: MIT
import os
import asyncio

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from .bot import bot
from .api import router

TOKEN = os.environ["DISCORD_TOKEN"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application."""
    app.state.httpClient = httpx.AsyncClient()
    botTask = asyncio.create_task(bot.start(TOKEN))
    try:
        yield
    finally:
        await bot.close()
        await app.state.httpClient.aclose()
        botTask.cancel()


app = FastAPI(lifespan=lifespan)
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "presence_cards.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
    )

