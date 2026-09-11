# SPDX-License-Identifier: MIT

from typing import Optional

import discord

from .store import Presence, store


def buildIntents() -> discord.Intents:
    intents = discord.Intents.default()
    intents.presences = True
    intents.members = True
    return intents


def extractServerTag(member: discord.Member) -> tuple[Optional[str], Optional[str]]:
    """Pull (tagText, badgeUrl) off a member's primary guild identity."""
    pg = getattr(member, "primary_guild", None)
    if pg is None or not pg.tag:
        return None, None
    if pg.identity_enabled is False:   # hide only on explicit False; None still shows
        return None, None
    badgeUrl = pg.badge.url if pg.badge else None
    return pg.tag, badgeUrl


class PresenceBot(discord.Client):
    async def on_ready(self):
        # Prime the store with whatever presences we can already see.
        for guild in self.guilds:
            for member in guild.members:
                self.capturePresence(member)
        print(f"Logged in as {self.user} — cached {len(store._presences)} presences.")

    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        self.capturePresence(after)

    def capturePresence(self, member: discord.Member) -> None:
        activityName = None
        if member.activities:
            for activity in member.activities:
                name = getattr(activity, "name", None)
                if name:
                    activityName = name
                    break

        tagText, badgeUrl = extractServerTag(member)

        # avatar decoration IS available from gateway user object
        decoUrl = None
        deco = getattr(member, "avatar_decoration", None)  # Asset or None
        if deco is not None:
            decoUrl = str(deco.url)

        store.updatePresence(
            Presence(
                userId=member.id,
                displayName=member.display_name,
                username=member.name,   # the @handle
                avatarUrl=str(member.display_avatar.replace(format="png", size=128).url),
                status=str(member.status),
                activityName=activityName,
                serverTagText=tagText,
                serverTagBadgeUrl=badgeUrl,
                avatarDecorationUrl=decoUrl,
                # bannerUrl intentionally NOT set here — needs REST fetch
            )
        )


bot = PresenceBot(intents=buildIntents())
