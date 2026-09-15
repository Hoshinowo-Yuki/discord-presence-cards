# SPDX-License-Identifier: MIT
"""Public helper surface. Renderers import from here, not the submodules."""

from .avatar import build_avatar_circle
from .pill import build_handle_pill_row, build_server_tag_pill
from .primitives import (
    FALLBACK_PNG_URI,
    FONT_STACK,
    build_text,
    escape_xml,
    estimate_text_width,
    fetch_data_uri,
)
from .status import STATUS_COLORS, build_status_indicator, resolve_status_color

__all__ = [
    # primitives
    "FALLBACK_PNG_URI",
    "FONT_STACK",
    "build_text",
    "escape_xml",
    "estimate_text_width",
    "fetch_data_uri",
    # status
    "STATUS_COLORS",
    "build_status_indicator",
    "resolve_status_color",
    # avatar
    "build_avatar_circle",
    # pill
    "build_server_tag_pill",
    "build_handle_pill_row",
]