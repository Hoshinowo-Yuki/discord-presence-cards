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
import discord
from ..bot import bot
from ..store import Presence

_user_cache: dict[int, discord.User] = {}

async def cached_fetch_user(user_id: int) -> Optional[discord.User]:
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Fetch a `discord.User` object from the cache, or via API if not cached.

    Parameters
    ----------
    user_id : int
        The Discord user ID to fetch.

    Returns
    -------
    discord.User, optional
        The `discord.User` object if found, otherwise `None`.
    """

    if user_id not in _user_cache:
        try:
            _user_cache[user_id] = await bot.fetch_user(user_id)

        except discord.HTTPException:
            return None

    return _user_cache[user_id]


async def enrich_presence(presence: Presence, user_id: int) -> None:
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Enrich a `Presence` object with additional user information, such as banner URL and accent color.

    Parameters
    ----------
    presence : Presence
        The `Presence` object to enrich.
    user_id : int
        The Discord user ID associated with the presence.

    Returns
    -------
    None
    """

    user = await cached_fetch_user(user_id)

    if user is None:
        return

    banner = user.banner

    if banner:
        presence.banner_url = str(
            banner.replace(
                format="gif" if banner.is_animated() else "png",
                size=1024,
            ).url
        )

    presence.accent_color = user.accent_color.value if user.accent_color else None
