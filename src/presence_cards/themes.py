# SPDX-License-Identifier: MIT

from typing import TypedDict, NotRequired

class Theme(TypedDict):
    background: str
    text: str
    subtext: str
    tagPill: str
    accent: str
    bgGradient: NotRequired[tuple[str, str]]   # (top, bottom); absent → flat fill


THEMES: dict[str, Theme] = {
    "dark": {
        "background": "#2f3136",
        "text":       "#ffffff",
        "subtext":    "#b9bbbe",
        "tagPill":    "#4f545c",
        "accent":     "#3ba55d",   # ← PICK THIS. seeded w/ Discord green; adjust
    },
    "light": {
        "background": "#ffffff",
        "text":       "#060607",
        "subtext":    "#4f5660",
        "tagPill":    "#e3e5e8",
        "accent":     "#248046",   # ← darker green so it reads on white
    },
}

DEFAULT_THEME = "dark"


def resolveTheme(name: str) -> Theme:
    return THEMES.get(name, THEMES[DEFAULT_THEME])