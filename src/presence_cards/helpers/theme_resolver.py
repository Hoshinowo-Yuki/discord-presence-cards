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

from typing import Optional
from ..themes import (
    Theme,
    resolveTheme,
    DEFAULT_THEME,
    TEXT_ON_DARK,
    TEXT_ON_LIGHT,
    ACCENT_GREEN,
)
from .color import luminance, shiftLightness, gradientFromColor


# Luminance below this reads as a dark surface (light text, lightening shifts).
_DARK_LUM_THRESHOLD = 0.5

# How far subtext and tag pills move off the background. Sign is applied at the
# call site: lighten on dark surfaces, darken on light ones.
_SUBTEXT_SHIFT      = 0.40
_PILL_SHIFT         = 0.12
_PILL_SHIFT_EXTREME = 0.22   # used when the accent is near-white/near-black

# A background counts as "extreme" outside this luminance band, where the normal
# pill shift would be too subtle to separate the pill from the background.
_EXTREME_LO = 0.15
_EXTREME_HI = 0.85


def themeFromGradient(top: str, bottom: str) -> Theme:
    """
    Build a theme from a two-stop gradient.

    The derived text, subtext, and tag-pill colors are keyed off the
    lighter of the two stops so contrast stays legible against the fade.

    Parameters
    ----------
    top : str
        The top gradient stop color.
    bottom : str
        The bottom gradient stop color, also used as the solid fallback
        background.

    Returns
    -------
    Theme
        The derived theme, including a "bgGradient" (top, bottom) pair.
    """

    lighterStop = top if luminance(top) > luminance(bottom) else bottom
    isDark = luminance(lighterStop) < _DARK_LUM_THRESHOLD

    return {
        "background": bottom,                 # solid fallback
        "bgGradient": (top, bottom),
        "text":    TEXT_ON_DARK if isDark else TEXT_ON_LIGHT,
        "subtext": shiftLightness(lighterStop, _SUBTEXT_SHIFT if isDark else -_SUBTEXT_SHIFT),
        "tagPill": shiftLightness(bottom, _PILL_SHIFT if isDark else -_PILL_SHIFT),
        "accent":  ACCENT_GREEN,
    }


def themeFromAccentBg(accentColor: Optional[int]) -> Theme:
    """
    Build a theme from a Discord accent color, or fall back to the default.

    The text, subtext, and tag-pill colors are derived from the accent. The
    pill shift is pushed harder when the accent is near an extreme (very
    light or very dark) so a near-white accent still yields a visibly
    distinct pill.

    Parameters
    ----------
    accentColor : Optional[int]
        The Discord accent color as a 24-bit integer, or None to use the
        default theme.

    Returns
    -------
    Theme
        The derived theme, or the resolved default theme when `accentColor`
        is None.
    """

    if accentColor is None:
        return resolveTheme(DEFAULT_THEME)

    background = f"#{accentColor:06x}"
    lum = luminance(background)
    isDark = lum < _DARK_LUM_THRESHOLD
    isExtreme = lum > _EXTREME_HI or lum < _EXTREME_LO
    pillShift = (_PILL_SHIFT_EXTREME if isDark else -_PILL_SHIFT_EXTREME) if isExtreme \
        else (_PILL_SHIFT if isDark else -_PILL_SHIFT)

    return {
        "background": background,
        "text":    TEXT_ON_DARK if isDark else TEXT_ON_LIGHT,
        "subtext": shiftLightness(background, _SUBTEXT_SHIFT if isDark else -_SUBTEXT_SHIFT),
        "tagPill": shiftLightness(background, pillShift),
        "accent":  ACCENT_GREEN,
    }


def resolveThemeParam(*, theme: str, color: Optional[str],
                      accentColor: Optional[int]) -> Theme:
    """
    Resolve the public theme parameters to a concrete Theme.

    Precedence is: an explicit `color` (gradient) wins, then `theme="accent"`
    (derived from `accentColor`), then a named theme.

    Parameters
    ----------
    theme : str
        The named theme, or "accent" to derive one from `accentColor`.
    color : Optional[str]
        An explicit gradient source color. When given, it takes precedence
        over everything else.
    accentColor : Optional[int]
        The Discord accent color, used only when `theme` is "accent".

    Returns
    -------
    Theme
        The resolved theme.
    """

    if color is not None:
        return themeFromGradient(*gradientFromColor(color))

    if theme == "accent":
        return themeFromAccentBg(accentColor)

    return resolveTheme(theme)
