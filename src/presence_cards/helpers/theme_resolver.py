from typing import Optional
from ..themes import Theme, resolveTheme, DEFAULT_THEME
from .color import luminance, shiftLightness, gradientFromColor


def themeFromGradient(top: str, bottom: str) -> Theme:
    worst = top if luminance(top) > luminance(bottom) else bottom   # lighter stop
    dark = luminance(worst) < 0.5
    return {
        "background": bottom,                 # solid fallback
        "bgGradient": (top, bottom),
        "text":    "#ffffff" if dark else "#060607",
        "subtext": shiftLightness(worst, 0.40 if dark else -0.40),
        "tagPill": shiftLightness(bottom, 0.12 if dark else -0.12),
        "accent":  "#3ba55d",
    }


def themeFromAccentBg(accentColor: Optional[int]) -> Theme:
    if accentColor is None:
        return resolveTheme(DEFAULT_THEME)
    bg = f"#{accentColor:06x}"
    lum = luminance(bg)
    dark = lum < 0.5
    extreme = lum > 0.85 or lum < 0.15        # near-white / near-black (your #f0f0f0)
    pill = (0.22 if dark else -0.22) if extreme else (0.12 if dark else -0.12)
    return {
        "background": bg,
        "text":    "#ffffff" if dark else "#060607",
        "subtext": shiftLightness(bg, 0.40 if dark else -0.40),
        "tagPill": shiftLightness(bg, pill),
        "accent":  "#3ba55d",
    }


def resolveThemeParam(*, theme: str, color: Optional[str],
                      accentColor: Optional[int]) -> Theme:
    """Precedence: color= (gradient) > theme=accent > named theme."""
    if color is not None:
        return themeFromGradient(*gradientFromColor(color))
    if theme == "accent":
        return themeFromAccentBg(accentColor)
    return resolveTheme(theme)