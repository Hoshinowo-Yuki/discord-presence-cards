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
A module for managing and resolving themes for the presence cards.

This module provides a way to define and use different themes for the presence cards,
allowing for a more visually appealing and consistent look across the application.
"""

from typing import TypedDict, NotRequired

class Theme(TypedDict):
    """
    A TypedDict representing a theme for the presence cards.

    Attributes
    ----------
    background : str
        The background color of the card.
    text : str
        The primary text color of the card.
    subtext : str
        The secondary text color of the card.
    tagPill : str
        The color of the tag pill on the card.
    accent : str
        The accent color used for highlights and important elements on the card.
    bgGradient : tuple of str, optional
        A tuple representing the top and bottom colors of a gradient background.
    """
    background: str
    text: str
    subtext: str
    tagPill: str
    accent: str
    bgGradient: NotRequired[tuple[str, str]]


# Canonical text colors for dark vs. light surfaces. Shared by the named themes
# below and by the resolver's derived (accent/gradient) themes, so "the text
# color for a dark surface" is defined in exactly one place.
# Note: editing these ripples into the resolver's computed text — that coupling
# is intentional.
TEXT_ON_DARK  = "#ffffff"
TEXT_ON_LIGHT = "#060607"

# The default brand accent, shared by the dark theme and every derived theme.
ACCENT_GREEN  = "#3ba55d"


THEMES: dict[str, Theme] = {
    "dark": {
        "background": "#2f3136",
        "text":       TEXT_ON_DARK,
        "subtext":    "#b9bbbe",
        "tagPill":    "#4f545c",
        "accent":     ACCENT_GREEN,
    },
    "light": {
        "background": "#ffffff",
        "text":       TEXT_ON_LIGHT,
        "subtext":    "#4f5660",
        "tagPill":    "#e3e5e8",
        "accent":     "#248046",   # deliberately darker than ACCENT_GREEN for contrast on white; left literal
    },
}

DEFAULT_THEME = "dark"


def resolveTheme(name: str) -> Theme:
    return THEMES.get(name, THEMES[DEFAULT_THEME])
