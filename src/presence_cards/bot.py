# SPDX-License-Identifier: MIT

import discord
from typing import Optional

from discord import Member, CustomActivity

from .helpers.badges import resolveBadges
from .store import Presence, store


def buildIntents() -> discord.Intents:
    intents = discord.Intents.default()
    intents.presences = True
    intents.members = True
    return intents

def extractCustomStatus(
    member: Member,
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """(text, emojiUnicode, emojiUrl). CustomActivity is orthogonal to rich
    activities — a user can have a game AND a custom status simultaneously,
    so we scan activities directly rather than reusing the ranked pick."""
    for act in member.activities:
        if isinstance(act, CustomActivity):
            emoji = act.emoji
            if emoji is None:
                return act.name, None, None
            if emoji.is_custom_emoji():
                return act.name, None, str(emoji.url)
            return act.name, emoji.name, None
    return None, None, None

def extractServerTag(member: Member) -> tuple[Optional[str], Optional[str]]:
    """Pull (tagText, badgeUrl) off a member's primary guild identity."""
    pg = getattr(member, "primary_guild", None)
    if pg is None or not pg.tag:
        return None, None
    if pg.identity_enabled is False:   # hide only on explicit False; None still shows
        return None, None
    badgeUrl = pg.badge.url if pg.badge else None
    return pg.tag, badgeUrl

def extractActivity(member: Member):
    empty = {
        "name": None, "details": None, "state": None,
        "largeImageUrl": None, "smallImageUrl": None, "start": None,
    }

    # CustomActivity is the status bubble, not a real activity for the box.
    candidates = [
        a for a in member.activities
        if not isinstance(a, CustomActivity)
    ]

    if not candidates:
        return empty

    def rank(a) -> int:
        n = type(a).__name__
        return {"Activity": 0, "Streaming": 1, "Spotify": 2, "Game": 3}.get(n, 4)

    act = sorted(candidates, key=rank)[0]
    if getattr(act, "name", None) is None:
        return empty

    return {
        "name": act.name,
        "details": getattr(act, "details", None),
        "state": getattr(act, "state", None),
        "largeImageUrl": getattr(act, "large_image_url", None),
        "smallImageUrl": getattr(act, "small_image_url", None),
        "start": getattr(act, "start", None),
    }

class PresenceBot(discord.Client):
    async def on_ready(self):
        # Prime the store with whatever presences we can already see.
        for guild in self.guilds:
            for member in guild.members:
                self.capturePresence(member)
        print(f"Logged in as {self.user} — cached {len(store._presences)} presences.")

    async def on_presence_update(self, before: Member, after: Member):
        self.capturePresence(after)

    def capturePresence(self, member: Member) -> None:
        act = extractActivity(member)

        tagText, badgeUrl = extractServerTag(member)
        statusText, statusEmojiUni, statusEmojiUrl = extractCustomStatus(member)

        decoUrl = None
        deco = getattr(member, "avatar_decoration", None)
        if deco is not None:
            decoUrl = str(deco.url)

        store.updatePresence(
            Presence(
                userId=member.id,
                displayName=member.display_name,
                username=member.name,
                avatarUrl=str(member.display_avatar.replace(format="png", size=128).url),
                status=str(member.status),
                activityName=act["name"],
                serverTagText=tagText,
                serverTagBadgeUrl=badgeUrl,
                avatarDecorationUrl=decoUrl,
                badgeUris=resolveBadges(member.public_flags),
                activityDetails=act["details"],
                activityState=act["state"],
                customStatusText=statusText,
                customStatusEmojiUnicode=statusEmojiUni,
                customStatusEmojiUrl=statusEmojiUrl,
                activityLargeImageUrl=act["largeImageUrl"],
                activitySmallImageUrl=act["smallImageUrl"],
                activityStart=act["start"],
            )
        )


bot = PresenceBot(intents=buildIntents())
