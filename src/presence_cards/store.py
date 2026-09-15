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
    user_id : int
        The Discord user ID.
    display_name : str
        The display name of the user.
    avatar_url : str
        The URL of the user's avatar.
    status : str
        The user's current status (e.g., "online", "idle", "dnd", "offline").
    activity_name : str, optional
        The name of the user's current activity, if any.
    server_tag_text : str, optional
        The text of the server tag, if any.
    server_tag_badge_url : str, optional
        The URL of the server tag badge, if any.
    username : str, optional
        The user's username (handle) under the display name.
    banner_url : str, optional
        The URL of the user's banner image, if any.
    avatar_decoration_url : str, optional
        The URL of the user's avatar decoration, if any.
    badge_uris : list of str
        A list of URIs for the user's badges.
    activity_details : str, optional
        The details of the user's current activity, if any.
    activity_state : str, optional
        The state of the user's current activity, if any.
    activity_large_image_url : str, optional
        The URL of the large image for the user's current activity, if any.
    activity_small_image_url : str, optional
        The URL of the small image for the user's current activity, if any.
    activity_start : datetime, optional
        The start time of the user's current activity, if any.
    custom_status_text : str, optional
        The text of the user's custom status, if any.
    custom_status_emoji_unicode : str, optional
        The Unicode representation of the emoji in the user's custom status, if any.
    custom_status_emoji_url : str, optional
        The URL of the emoji in the user's custom status, if any.
    accent_color : int, optional
        The accent color of the user's profile, if any.

    Notes
    -----
    This dataclass is flattened intentionally, making it easier to serialize and store in a database or cache.
    """

    user_id: int
    display_name: str
    avatar_url: str
    status: str  # "online" | "idle" | "dnd" | "offline"
    activity_name: Optional[str] = None

    server_tag_text: Optional[str] = None      # the pill text, e.g. "GG"
    server_tag_badge_url: Optional[str] = None  # CDN url for the emblem, or None

    # --- profile-card fields (populate these in bot.py) ---
    username: Optional[str] = None            # @handle under the display name
    banner_url: Optional[str] = None           # animated .gif ok, needs base64'd
    avatar_decoration_url: Optional[str] = None # APNG preset, needs base64'd
    badge_uris: list[str] = field(default_factory=list)  # from resolve_badges(user.public_flags)

    # --- activity row (also populate in bot.py, from the dpy Activity) ---
    activity_details: Optional[str] = None       # first text line under name
    activity_state: Optional[str] = None         # second text line
    activity_large_image_url: Optional[str] = None # from Activity.large_image_url
    activity_small_image_url: Optional[str] = None # from Activity.small_image_url
    activity_start: Optional[datetime] = None    # from Activity.start (tz-aware)

    # --- custom status (also populate in bot.py, from the dpy CustomActivity) ---
    custom_status_text: Optional[str] = None
    custom_status_emoji_unicode: Optional[str] = None
    custom_status_emoji_url: Optional[str] = None

    accent_color: Optional[int] = None    # user.accent_color.value or None


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
    update_presence(presence)
        Update the presence information for a user.
    get_presence(user_id)
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



    def update_presence(self, presence: Presence) -> None:
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

        self._presences[presence.user_id] = presence



    def get_presence(self, user_id: int) -> Optional[Presence]:
        """
        Retrieves the presence information for a user by their Discord user ID.

        Parameters
        ----------
        user_id : int
            The Discord user ID of the user whose presence information is to be retrieved.
        
        Returns
        -------
        Presence, optional
            An instance of the `Presence` dataclass containing the user's presence information,
            or `None` if no presence information is found for the given user ID.
        """
        return self._presences.get(user_id)


# Single shared instance, imported by both the bot and the API.
store = PresenceStore()