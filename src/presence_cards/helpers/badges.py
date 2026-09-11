# SPDX-License-Identifier: MIT
"""Maps Discord public_flags → local badge SVGs and loads them as data URIs.

Badge SVGs live in ../assets/badges/ and are MIT-licensed (see NOTICE there).
"""

import base64
from functools import lru_cache
from pathlib import Path

from discord import UserFlags

_BADGE_DIR = Path(__file__).parent.parent.parent / "assets" / "badges"

if not _BADGE_DIR.is_dir():
    raise RuntimeError(
        f"Badge dir not found: {_BADGE_DIR}. "
        f"Check _BADGE_DIR depth relative to helpers/badges.py."
    )

# Order here == render order (left to right). Discord's own ordering is
# roughly staff → partner → hypesquad → bug hunters → supporter, so we mirror it.
BADGE_MAP: dict[UserFlags, str] = {
    UserFlags.staff: "Staff.svg",
    UserFlags.partner: "Partner.svg",
    UserFlags.hypesquad: "Hypesquad.svg",
    UserFlags.hypesquad_bravery: "HypeSquadOnlineHouse1.svg",
    UserFlags.hypesquad_brilliance: "HypeSquadOnlineHouse2.svg",
    UserFlags.hypesquad_balance: "HypeSquadOnlineHouse3.svg",
    UserFlags.bug_hunter: "BugHunterLevel1.svg",
    UserFlags.bug_hunter_level_2: "BugHunterLevel2.svg",
    UserFlags.early_supporter: "PremiumEarlySupporter.svg",
    UserFlags.verified_bot_developer: "VerifiedDeveloper.svg", # retired 2020; only pre-existing holders still carry it.

    # active_developer → decommissioned & stripped from profiles 2025-12-05,
    #                    flag no longer returned by API. SVG kept in assets/.
    # premium (Nitro)  → not a public flag; undetectable for other users.
    # moderator_programs_alumni → flaky/deprecated; SVG kept but unmapped.
}


@lru_cache(maxsize=None)
def _loadBadgeUri(filename: str) -> str:
    """Read a badge SVG from disk and return it as a base64 data URI. Cached."""
    raw = (_BADGE_DIR / filename).read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def resolveBadges(flags) -> list[str]:
    """Given a user's public_flags, return badge data URIs in render order.

    `flags` is a discord.PublicUserFlags (has .all() → list[UserFlags]).
    Iterates BADGE_MAP (not flags) so output order is stable & controlled.
    """
    present = set(flags.all())
    return [
        _loadBadgeUri(fname)
        for flag, fname in BADGE_MAP.items()
        if flag in present
    ]

