# SPDX-License-Identifier: MIT
"""Theme resolution: map the public theme/color/accent params to a Theme."""

from typing import Optional
from ..themes import Theme, resolveTheme, DEFAULT_THEME
from .color import luminance, shiftLightness, gradientFromColor


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
    isDark = luminance(lighterStop) < 0.5

    return {
        "background": bottom,                 # solid fallback
        "bgGradient": (top, bottom),
        "text":    "#ffffff" if isDark else "#060607",
        "subtext": shiftLightness(lighterStop, 0.40 if isDark else -0.40),
        "tagPill": shiftLightness(bottom, 0.12 if isDark else -0.12),
        "accent":  "#3ba55d",
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
    isDark = lum < 0.5
    isExtreme = lum > 0.85 or lum < 0.15      # near-white / near-black (e.g. #f0f0f0)
    pillShift = (0.22 if isDark else -0.22) if isExtreme else (0.12 if isDark else -0.12)

    return {
        "background": background,
        "text":    "#ffffff" if isDark else "#060607",
        "subtext": shiftLightness(background, 0.40 if isDark else -0.40),
        "tagPill": shiftLightness(background, pillShift),
        "accent":  "#3ba55d",
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