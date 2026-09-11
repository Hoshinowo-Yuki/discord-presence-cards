# SPDX-License-Identifier: MIT

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Presence:
    userId: int
    displayName: str
    avatarUrl: str
    status: str  # "online" | "idle" | "dnd" | "offline"
    activityName: Optional[str] = None

    serverTagText: Optional[str] = None      # the pill text, e.g. "GG"
    serverTagBadgeUrl: Optional[str] = None  # CDN url for the emblem, or None

    # --- profile-card fields (populate these in bot.py) ---
    username: Optional[str] = None            # @handle under the display name
    bannerUrl: Optional[str] = None           # animated .gif ok → base64'd
    avatarDecorationUrl: Optional[str] = None # APNG preset → base64'd
    badgeUris: list[str] = field(default_factory=list)  # from resolveBadges(user.public_flags)

    # --- activity row (also populate in bot.py, from the dpy Activity) ---
    activityDetails: Optional[str] = None       # first text line under name
    activityState: Optional[str] = None         # second text line
    activityLargeImageUrl: Optional[str] = None # from Activity.large_image_url
    activitySmallImageUrl: Optional[str] = None # from Activity.small_image_url
    activityStart: Optional[datetime] = None    # from Activity.start (tz-aware)

    accentColor: Optional[int] = None    # user.accent_color.value or None

class PresenceStore:
    """In-memory presence store, keyed by Discord user id."""

    def __init__(self):
        self._presences: dict[int, Presence] = {}

    def updatePresence(self, presence: Presence) -> None:
        self._presences[presence.userId] = presence

    def getPresence(self, userId: int) -> Optional[Presence]:
        return self._presences.get(userId)


# Single shared instance, imported by both the bot and the API.
store = PresenceStore()