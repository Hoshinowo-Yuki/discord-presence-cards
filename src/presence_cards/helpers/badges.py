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
A helper for mapping Discord public_flags to local badge SVGs and loads them as data URIs.

Badge SVGs live in `../assets/badges/` and are MIT-licensed (see NOTICE there).
"""

import base64
from functools import lru_cache
from presence_cards import BADGE_DIR
from discord import UserFlags

if not BADGE_DIR.is_dir():
    raise RuntimeError(
        f"Badge dir not found: {BADGE_DIR}. "
        f"Check _BADGE_DIR depth relative to helpers/badges.py."
    )

# Order here == render order (left to right). Discord's own ordering is
# roughly staff -> partner -> hypesquad -> bug hunters -> supporter, so we mirror it.
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

    # active_developer -> decommissioned & stripped from profiles 2025-12-05,
    #                    flag no longer returned by API. SVG kept in assets/.
    # premium (Nitro)  -> not a public flag; undetectable for other users.
    # moderator_programs_alumni -> flaky/deprecated; SVG kept but unmapped.
}


@lru_cache(maxsize=None)
def _load_badge_uri(filename: str) -> str:
    """
    Read a badge SVG from disk and return it as a base64 data URI. 

    Parameters
    ----------
    filename : str
        The filename of the badge SVG in the assets/badges directory.

    Returns
    -------
    str
        A base64-encoded data URI of the badge SVG.
    """

    raw = (BADGE_DIR / filename).read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def resolve_badges(flags) -> list[str]:
    """
    Return a list of badge data URIs for the given Discord public_flags, in render order.

    Parameters
    ----------
    flags : discord.UserFlags
        The public flags of a Discord user.

    Returns
    -------
    list of str
        A list of data URIs for the user's badges, in the order they should be rendered.
    """

    present = set(flags.all())
    return [
        _load_badge_uri(fname)
        for flag, fname in BADGE_MAP.items()
        if flag in present
    ]

