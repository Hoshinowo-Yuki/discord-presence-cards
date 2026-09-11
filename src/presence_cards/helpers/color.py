# SPDX-License-Identifier: MIT
"""Color derivations. Panels are computed from the theme background so any
user theme gets a correct raised-card color without declaring one."""

from typing import Optional
from ..themes import Theme, resolveTheme, DEFAULT_THEME

_NAMED = {"blurple": "#5865f2", "green": "#3ba55d", "red": "#ed4245", "blue": "#3b82f6"}

def normalizeHex(raw: str) -> str:
    s = raw.strip().lstrip("#").lower()
    if s in _NAMED:
        return _NAMED[s]
    s = s.removeprefix("0x")
    if len(s) == 3:                                   # "f0a" → "ff00aa"
        s = "".join(c * 2 for c in s)
    if len(s) != 6 or any(c not in "0123456789abcdef" for c in s):
        raise ValueError(f"bad color: {raw!r}")
    return f"#{s}"

def gradientFromColor(raw: str) -> tuple[str, str]:
    """One input color → (top, bottom) stops for a dark→light fade."""
    base = normalizeHex(raw)                          # raises ValueError on junk
    if luminance(base) < 0.5:
        return base, shiftLightness(base, 0.28)       # dark base → fade lighter
    return shiftLightness(base, -0.28), base          # light base → fade darker

def themeFromAccentBg(accent_color: Optional[int]) -> Theme:
    if accent_color is None:
        return resolveTheme(DEFAULT_THEME)
    bg = f"#{accent_color:06x}"
    lum = luminance(bg)
    dark = lum < 0.5

    # push toward the opposite end; bigger push when bg is near an extreme
    # so a near-white (#f0f0f0) still yields a visibly darker pill/subtext.
    subShift  = (-0.45 if not dark else 0.45)
    pillShift = (-0.18 if not dark else 0.18)

    return {
        "background": bg,
        "text":    "#060607" if not dark else "#ffffff",
        "subtext": shiftLightness(bg, subShift),
        "tagPill": shiftLightness(bg, pillShift),
        "accent":  "#3ba55d",
    }

def _hexToRgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgbToHex(r: float, g: float, b: float) -> str:
    c = lambda v: max(0, min(255, round(v)))
    return f"#{c(r):02x}{c(g):02x}{c(b):02x}"


def luminance(hexColor: str) -> float:
    r, g, b = _hexToRgb(hexColor)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255


def shiftLightness(hexColor: str, amount: float) -> str:
    """Nudge toward white (amount>0) or black (amount<0)."""
    r, g, b = _hexToRgb(hexColor)
    if amount >= 0:
        r += (255 - r) * amount
        g += (255 - g) * amount
        b += (255 - b) * amount
    else:
        f = 1 + amount
        r *= f; g *= f; b *= f
    return _rgbToHex(r, g, b)


def derivePanel(background: str, amount: float = 0.06) -> str:
    """Raised-card color: lighten on dark themes, darken on light themes."""
    return shiftLightness(background, amount if luminance(background) < 0.5 else -amount)