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
Raw custom-status extraction.

Convention
----------

`discord.py` normalizes an emoji-only status with name="Custom Status" into both
activity.name and activity.state, losing that `state` was absent in Discord's
original payload. We track the raw `state` field per user straight off the
gateway so a user who literally typed "Custom Status" stays distinguishable.
"""

import json
from typing import Optional

# We won't use dpy here to fetch the custom status, but still needs their Member and CustomActivity types for type hints.
from discord import Member, CustomActivity

# Constants for identifying the PRESENCE_UPDATE event and custom activity type
_PRESENCE_UPDATE = "PRESENCE_UPDATE"
_CUSTOM_ACTIVITY_TYPE = 4


def extractCustomStatus(
    member: Member,
    rawText: Optional[str] = None,
    hasRawPayload: bool = False,
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract the custom status from a Member object.

    Parameters
    ----------
    member : discord.Member
        The member from which to extract the custom status.
    rawText : Optional[str], optional
        The raw custom status text, if available. Defaults to None.
    hasRawPayload : bool, optional
        Whether the raw payload was available. Defaults to False.

    Returns
    -------
    tuple of str, optional
        A tuple containing the custom status text, emoji unicode and emoji URL,
        or None if not available.
    """

    # (text, emojiUnicode, emojiUrl)
    # CustomActivity is orthogonal to rich activities 
    # A user can have a game AND a custom status simultaneously,
    # so we scan activities directly rather than reusing the ranked pick.

    for act in member.activities:
        if isinstance(act, CustomActivity):
            emoji = act.emoji
            text = rawText if hasRawPayload else (act.state or "")

            if emoji is None:
                return text, None, None

            if emoji.is_custom_emoji():
                return text, None, str(emoji.url)

            return text, emoji.name, None

    return None, None, None


class RawCustomStatusTracker:
    """
    Raw custom-status tracker from the gateway level.

    This caches the raw custom-status `state` per user id. populated from the
    gateway before dpy can normalize it away.

    Parameters
    ----------
    _rawText : dict[int, Optional[str]]
        A dictionary mapping user IDs to their raw custom-status text.

    Methods
    -------
    ingest(msg)
        Feed a raw gateway frame. No-op unless it's a PRESENCE_UPDATE.
    resolve(member)
        Resolve the custom status for a member, using raw-tracked text when available.
    """

    def __init__(self) -> None:
        self._rawText: dict[int, Optional[str]] = {}


    def ingest(self, msg: str) -> None:
        """
        Feed a raw gateway frame.
        
        No-op unless it's a PRESENCE_UPDATE.

        Parameters
        ----------
        msg : str
            The raw gateway frame as a JSON string.
        """

        if f'"{_PRESENCE_UPDATE}"' not in msg:
            return

        # Check if the message is a PRESENCE_UPDATE event
        payload = json.loads(msg)
        if payload.get("t") != _PRESENCE_UPDATE:
            return

        # Extract the raw custom-status text from the payload and store it in `_rawText`
        data = payload.get("d", {})

        customActivities = [
            activity
            for activity in data.get("activities", [])
            if activity.get("type") == _CUSTOM_ACTIVITY_TYPE
        ]

        userId = int(data.get("user", {}).get("id", 0))

        if customActivities:
            self._rawText[userId] = customActivities[0].get("state")

        elif userId:
            self._rawText[userId] = None


    def resolve(
        self, member: Member
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Resolve the custom status for a member, using raw-tracked text when available.

        Parameters
        ----------
        member : discord.Member
            The member from which to extract the custom status.

        Returns
        -------
        tuple of str, optional
            A tuple containing the custom status text, emoji unicode and emoji URL,
            or None if not available.
        """
        
        return extractCustomStatus(
            member,
            rawText=self._rawText.get(member.id),
            hasRawPayload=member.id in self._rawText,
        )

