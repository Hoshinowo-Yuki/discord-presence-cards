# SPDX-License-Identifier: MIT
import os
import asyncio
import httpx

from contextlib import asynccontextmanager, suppress
from fastapi import FastAPI
from .bot import bot
from .api import router

TOKEN = os.environ["DISCORD_TOKEN"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application."""
    app.state.http_client = httpx.AsyncClient()
    bot_task = asyncio.create_task(bot.start(TOKEN))

    # Fail loudly if the bot can't connect, instead of serving an empty store.
    ready = asyncio.create_task(bot.wait_until_ready())
    done, _ = await asyncio.wait(
        {ready, bot_task},
        return_when=asyncio.FIRST_COMPLETED
    )
    if bot_task in done:            # start() returned/raised before ready
        bot_task.result()          # re-raises the real error (e.g. LoginFailure)

    try:
        yield
    finally:
        await bot.close()
        bot_task.cancel()
        with suppress(asyncio.CancelledError):
            await bot_task


app = FastAPI(lifespan=lifespan)
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "presence_cards.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
    )
