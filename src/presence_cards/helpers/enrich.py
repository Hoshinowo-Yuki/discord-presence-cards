from typing import Optional
import discord
from ..bot import bot
from ..store import Presence

_userCache: dict[int, discord.User] = {}

async def cachedFetchUser(userId: int) -> Optional[discord.User]:
    if userId not in _userCache:
        try:
            _userCache[userId] = await bot.fetch_user(userId)
        except discord.HTTPException:
            return None
    return _userCache[userId]

async def enrichPresence(presence: Presence, userId: int) -> None:
    user = await cachedFetchUser(userId)
    if user is None:
        return
    if user.banner:
        presence.bannerUrl = str(user.banner.replace(format="png", size=1024).url)
    presence.accentColor = user.accent_color.value if user.accent_color else None