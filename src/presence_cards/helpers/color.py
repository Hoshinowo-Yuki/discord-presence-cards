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
Color derivations. 

Panels are computed from the theme background so any user theme
gets a correct raised-card color without declaring one.
"""

from typing import Optional
from ..themes import Theme, resolveTheme, DEFAULT_THEME

_NAMED_COLORS = {
    "blurple": "#5865f2",
    "green": "#3ba55d",
    "red": "#ed4245",
    "blue": "#3b82f6",
}


def normalizeHex(raw: str) -> str:
    """
    Normalize a color string to a canonical "#rrggbb" hex value.

    Accepts named colors, an optional leading "#" or "0x", and both the
    3- and 6-digit hex forms.

    Parameters
    ----------
    raw : str
        The raw color string, e.g. "blurple", "#f0a", or "0xFF00AA".

    Returns
    -------
    str
        The normalized color as a lowercase "#rrggbb" string.

    Raises
    ------
    ValueError
        If the string is not a known name or a valid 3- or 6-digit hex.
    """

    value = raw.strip().lstrip("#").lower()
    if value in _NAMED_COLORS:
        return _NAMED_COLORS[value]

    value = value.removeprefix("0x")

    if len(value) == 3:                                   # "f0a" -> "ff00aa"
        value = "".join(ch * 2 for ch in value)

    if len(value) != 6 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError(f"bad color: {raw!r}")

    return f"#{value}"


def gradientFromColor(raw: str) -> tuple[str, str]:
    """
    Derive a two-stop gradient from a single input color.

    Parameters
    ----------
    raw : str
        The input color, in any form accepted by `normalizeHex`.

    Returns
    -------
    tuple of (str, str)
        The (top, bottom) gradient stops for a dark-to-light fade. A dark
        base fades lighter toward the bottom; a light base fades darker.

    Raises
    ------
    ValueError
        If `raw` is not a valid color (propagated from `normalizeHex`).
    """

    base = normalizeHex(raw)                          # raises ValueError on junk

    if luminance(base) < 0.5:
        return base, shiftLightness(base, 0.28)       # dark base -> fade lighter

    return shiftLightness(base, -0.28), base          # light base -> fade darker


def themeFromAccentColor(accentColor: Optional[int]) -> Theme:
    """
    Build a theme from a Discord accent color, or fall back to the default.

    The text, subtext, and tag-pill colors are derived from the accent so
    the result stays legible whether the accent is dark or light.

    Shifts are pushed toward the opposite end of the lightness range, and pushed
    harder when the accent is near an extreme, so a near-white accent still
    yields a visibly darker pill and subtext.

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
    isDark = luminance(background) < 0.5

    subtextShift = 0.45 if isDark else -0.45
    pillShift = 0.18 if isDark else -0.18

    return {
        "background": background,
        "text":    "#ffffff" if isDark else "#060607",
        "subtext": shiftLightness(background, subtextShift),
        "tagPill": shiftLightness(background, pillShift),
        "accent":  "#3ba55d",
    }


def _hexToRgb(hexColor: str) -> tuple[int, int, int]:
    """
    Convert a hex color to an (r, g, b) tuple.

    Parameters
    ----------
    hexColor : str
        A hex color with an optional leading "#", in 3- or 6-digit form.

    Returns
    -------
    tuple of (int, int, int)
        The red, green, and blue channels, each in the range 0-255.
    """

    hexColor = hexColor.lstrip("#")

    if len(hexColor) == 3:
        hexColor = "".join(ch * 2 for ch in hexColor)

    return int(hexColor[0:2], 16), int(hexColor[2:4], 16), int(hexColor[4:6], 16)


def _rgbToHex(r: float, g: float, b: float) -> str:
    """
    Convert r, g, b channels to a "#rrggbb" hex string.

    Parameters
    ----------
    r : float
        The red channel; rounded and clamped to 0-255.
    g : float
        The green channel; rounded and clamped to 0-255.
    b : float
        The blue channel; rounded and clamped to 0-255.

    Returns
    -------
    str
        The color as a lowercase "#rrggbb" string.
    """

    clamp = lambda value: max(0, min(255, round(value)))
    return f"#{clamp(r):02x}{clamp(g):02x}{clamp(b):02x}"


def luminance(hexColor: str) -> float:
    """
    Compute the relative luminance of a color.

    Parameters
    ----------
    hexColor : str
        The color to measure, in any form accepted by `_hexToRgb`.

    Returns
    -------
    float
        The luminance in the range 0.0 (black) to 1.0 (white), using the
        Rec. 709 channel weights.
    """

    r, g, b = _hexToRgb(hexColor)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255


def shiftLightness(hexColor: str, amount: float) -> str:
    """
    Nudge a color toward white or black.

    Parameters
    ----------
    hexColor : str
        The color to shift, in any form accepted by `_hexToRgb`.
    amount : float
        The shift fraction. Positive values blend toward white; negative
        values scale toward black. Expected range is -1.0 to 1.0.

    Returns
    -------
    str
        The shifted color as a "#rrggbb" string.
    """

    r, g, b = _hexToRgb(hexColor)

    if amount >= 0:
        r += (255 - r) * amount
        g += (255 - g) * amount
        b += (255 - b) * amount

    else:
        factor = 1 + amount
        r *= factor
        g *= factor
        b *= factor

    return _rgbToHex(r, g, b)


def derivePanel(background: str, amount: float = 0.06) -> str:
    """
    Derive a raised-card color from a theme background.

    Parameters
    ----------
    background : str
        The theme background color, in any form accepted by `_hexToRgb`.
    amount : float, optional
        The lightness shift magnitude (default is 0.06).

    Returns
    -------
    str
        The panel color: lightened on dark backgrounds, darkened on light
        ones, so the card always reads as raised above the background.
    """

    return shiftLightness(background, amount if luminance(background) < 0.5 else -amount)
