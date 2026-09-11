# SPDX-License-Identifier: MIT

from typing import TypedDict


class Theme(TypedDict):
    background: str
    text: str
    subtext: str
    tagPill: str


THEMES: dict[str, Theme] = {
    "dark": {
        "background": "#2f3136",
        "text": "#ffffff",
        "subtext": "#b9bbbe",
        "tagPill": "#4f545c",
    },
    "light": {
        "background": "#ffffff",
        "text": "#060607",
        "subtext": "#4f5660",
        "tagPill": "#e3e5e8",
    },
}

DEFAULT_THEME = "dark"


def resolveTheme(name: str) -> Theme:
    """Return the requested theme, falling back to the default if unknown."""
    return THEMES.get(name, THEMES[DEFAULT_THEME])