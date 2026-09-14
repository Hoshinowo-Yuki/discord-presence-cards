# The MIT License (MIT)
#
# Copyright (c) 2026 Hoshino Yuki
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
# SPDX-License-Identifier: MIT

"""
A module for storing and managing user presence information.

This module provides a way to store and retrieve user presence information,
including their status, activities, and custom status.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Presence:
    """
    Representing a user's presence information.

    Attributes
    ----------
    userId : int
        The Discord user ID.
    displayName : str
        The display name of the user.
    avatarUrl : str
        The URL of the user's avatar.
    status : str
        The user's current status (e.g., "online", "idle", "dnd", "offline").
    activityName : str, optional
        The name of the user's current activity, if any.
    serverTagText : str, optional
        The text of the server tag, if any.
    serverTagBadgeUrl : str, optional
        The URL of the server tag badge, if any.
    username : str, optional
        The user's username (handle) under the display name.
    bannerUrl : str, optional
        The URL of the user's banner image, if any.
    avatarDecorationUrl : str, optional
        The URL of the user's avatar decoration, if any.
    badgeUris : list of str
        A list of URIs for the user's badges.
    activityDetails : str, optional
        The details of the user's current activity, if any.
    activityState : str, optional
        The state of the user's current activity, if any.
    activityLargeImageUrl : str, optional
        The URL of the large image for the user's current activity, if any.
    activitySmallImageUrl : str, optional
        The URL of the small image for the user's current activity, if any.
    activityStart : datetime, optional
        The start time of the user's current activity, if any.
    customStatusText : str, optional
        The text of the user's custom status, if any.
    customStatusEmojiUnicode : str, optional
        The Unicode representation of the emoji in the user's custom status, if any.
    customStatusEmojiUrl : str, optional
        The URL of the emoji in the user's custom status, if any.
    accentColor : int, optional
        The accent color of the user's profile, if any.

    Notes
    -----
    This dataclass is flattened intentionally, making it easier to serialize and store in a database or cache.
    """

    userId: int
    displayName: str
    avatarUrl: str
    status: str  # "online" | "idle" | "dnd" | "offline"
    activityName: Optional[str] = None

    serverTagText: Optional[str] = None      # the pill text, e.g. "GG"
    serverTagBadgeUrl: Optional[str] = None  # CDN url for the emblem, or None

    # --- profile-card fields (populate these in bot.py) ---
    username: Optional[str] = None            # @handle under the display name
    bannerUrl: Optional[str] = None           # animated .gif ok, needs base64'd
    avatarDecorationUrl: Optional[str] = None # APNG preset, needs base64'd
    badgeUris: list[str] = field(default_factory=list)  # from resolveBadges(user.public_flags)

    # --- activity row (also populate in bot.py, from the dpy Activity) ---
    activityDetails: Optional[str] = None       # first text line under name
    activityState: Optional[str] = None         # second text line
    activityLargeImageUrl: Optional[str] = None # from Activity.large_image_url
    activitySmallImageUrl: Optional[str] = None # from Activity.small_image_url
    activityStart: Optional[datetime] = None    # from Activity.start (tz-aware)

    # --- custom status (also populate in bot.py, from the dpy CustomActivity) ---
    customStatusText: Optional[str] = None
    customStatusEmojiUnicode: Optional[str] = None
    customStatusEmojiUrl: Optional[str] = None

    accentColor: Optional[int] = None    # user.accent_color.value or None


class PresenceStore:
    """
    In-memory presence store keyed by Discord user id.

    This uses our `Presence` dataclass.

    Attributes
    ----------
    _presences : dict[int, Presence]
        A dictionary mapping user IDs to their presence information.
    
    Methods
    -------
    updatePresence(presence)
        Update the presence information for a user.
    getPresence(userId)
        Retrieve the presence information for a user by their ID.

    Notes
    -----
    This store is intended to be a single shared instance, imported by both the bot and the
    API. It allows for efficient retrieval and updating of user presence information without
    the need for repeated API calls to Discord.

    In this way we could capture various aspects of a user's presence, including their status,
    activities and custom status in one place, without the need on calling discord's API
    multiple times.
    """

    def __init__(self):
        self._presences: dict[int, Presence] = {}


    def updatePresence(self, presence: Presence) -> None:
        """
        Updates the presence information for a user in the store.

        Parameters
        ----------
        presence : Presence
            An instance of the `Presence` dataclass containing the user's presence information.
        
        Returns
        -------
        None
        """

        self._presences[presence.userId] = presence


    def getPresence(self, userId: int) -> Optional[Presence]:
        """
        Retrieves the presence information for a user by their Discord user ID.

        Parameters
        ----------
        userId : int
            The Discord user ID of the user whose presence information is to be retrieved.
        
        Returns
        -------
        Presence, optional
            An instance of the `Presence` dataclass containing the user's presence information,
            or `None` if no presence information is found for the given user ID.
        """
        return self._presences.get(userId)


# Single shared instance, imported by both the bot and the API.
store = PresenceStore()
