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

import discord
from typing import Optional
from discord import Client, Member, CustomActivity
from .rawCustomStatus import RawCustomStatusTracker
from .helpers.badges import resolveBadges
from .store import Presence, store


def buildIntents() -> discord.Intents:
    """Build a discord.Intents object with the necessary flags for presence tracking."""
    intents = discord.Intents.default()
    intents.presences = True
    intents.members = True

    return intents


def extractServerTag(member: Member) -> tuple[Optional[str], Optional[str]]:
    """
    Extract the server tag text and badge URL from a Member's primary guild identity.

    Parameters
    ----------
    member : discord.Member
        The member from which to extract the server tag and badge.

    Returns
    -------
    tuple of str, optional
        A tuple containing the server tag text and badge URL,
        or None if not available.
    """

    # Pull (tagText, badgeUrl) off a member's primary guild identity.
    pg = getattr(member, "primary_guild", None)
    if pg is None or not pg.tag:
        return None, None

    if pg.identity_enabled is False:   # hide only on explicit False; None still shows
        return None, None

    badgeUrl = pg.badge.url if pg.badge else None
    return pg.tag, badgeUrl


def extractActivity(member: Member):
    """
    Extract the most relevant activity from a Member's activities, ignoring CustomActivity.

    Parameters
    ----------
    member : discord.Member
        The member from which to extract the activity.

    Returns
    -------
    dict
        A dictionary containing the activity's name, details, state, large image URL, small image
        URL, and start time, or None if not available.
    """

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


class PresenceBot(Client):
    """
    Client connector that tracks presences and raw custom-status text, and caches them in `store`.
    
    Attributes
    ----------
    customStatus : RawCustomStatusTracker
        A tracker for raw custom-status text, populated from the gateway before dpy normalizes it

    Methods
    -------
    on_socket_raw_receive(msg) -> None
        Feed a raw gateway frame to the custom-status tracker.

    on_ready() -> None
        Prime the store with whatever presences we can already see.

    on_presence_update(before, after) -> None
        Capture the updated presence of a member.

    capturePresence(member) -> None
        Extract relevant presence fields from a Member and update the store.
    
    Notes
    -----
    This class is a data-layer class, not a card-rendering class. It does not know about
    themes, colors, or SVGs. It only knows about Discord presences and how to extract
    the relevant fields for rendering.

    It is intended to be used in a long-running process that maintains a connection
    to the Discord gateway, so that it can receive presence updates in real-time.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.customStatus = RawCustomStatusTracker()


    async def on_socket_raw_receive(self, msg: str) -> None:
        """
        This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

        Called whenever a raw gateway frame is received.

        Parameters
        ----------
        msg : str
            The raw JSON string of the gateway frame.

        Returns
        -------
        None

        Notes
        -----
        This function feeds the raw gateway frame to the custom-status tracker, which
        will extract any raw custom-status text and cache it for later use.
        """

        self.customStatus.ingest(msg)


    async def on_ready(self):
        """
        This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

        Displaying startup info.

        Returns
        -------
        None
        """

        # Prime the store with whatever presences we can already see.
        for guild in self.guilds:
            for member in guild.members:
                self.capturePresence(member)
        print(f"Logged in as {self.user} — cached {len(store._presences)} presences.")


    async def on_presence_update(self, before: Member, after: Member):
        """
        This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

        Called whenever a member's presence is updated.

        This includes changes to their status, activity, or custom status.

        Parameters
        ----------
        before : discord.Member
            The member before the presence update, we left it unused for now.
        after : discord.Member
            The member after the presence update.

        Returns
        -------
        None
        """

        self.capturePresence(after)


    def capturePresence(self, member: Member) -> None:
        """
        Extract relevant presence fields from a Member and update the store.

        Parameters
        ----------
        member : discord.Member
            The member whose presence is being captured.

        Returns
        -------
        None
        """

        act = extractActivity(member)

        avatar = member.display_avatar
        tagText, badgeUrl = extractServerTag(member)
        statusText, statusEmojiUni, statusEmojiUrl = self.customStatus.resolve(member)

        decoUrl = None
        deco = getattr(member, "avatar_decoration", None)
        if deco is not None:
            decoUrl = str(deco.url)

        store.updatePresence(
            Presence(
                userId=member.id,
                displayName=member.display_name,
                username=member.name,
                avatarUrl = str(
                    avatar.replace(
                        format="gif" if avatar.is_animated() else "png",
                        size=128
                        )
                    .url
                ),
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
