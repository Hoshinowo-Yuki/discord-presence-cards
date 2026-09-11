# SPDX-License-Identifier: MIT
"""Public helper surface. Renderers import from here, not the submodules."""

from .avatar import buildAvatarCircle
from .pill import buildHandlePillRow, buildServerTagPill
from .primitives import (
    FALLBACK_PNG_URI,
    FONT_STACK,
    buildText,
    escapeXml,
    estimateTextWidth,
    fetchDataUri,
)
from .status import STATUS_COLORS, buildStatusIndicator, resolveStatusColor

__all__ = [
    # primitives
    "FALLBACK_PNG_URI",
    "FONT_STACK",
    "buildText",
    "escapeXml",
    "estimateTextWidth",
    "fetchDataUri",
    # status
    "STATUS_COLORS",
    "buildStatusIndicator",
    "resolveStatusColor",
    # avatar
    "buildAvatarCircle",
    # pill
    "buildServerTagPill",
    "buildHandlePillRow",
]