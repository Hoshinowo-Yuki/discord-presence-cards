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

from fastapi import Response

_NOT_FOUND_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' width='340' height='120'>"
    "<rect width='340' height='120' rx='12' fill='#2f3136'/>"
    "<text x='24' y='64' fill='#b9bbbe' font-family='sans-serif' font-size='16'>"
    "Presence not found</text></svg>"
)

def notFoundCard() -> Response:
    """Not found response for a presence card request."""
    return Response(
        content=_NOT_FOUND_SVG,
        media_type="image/svg+xml",
        status_code=404
    )

def svgResponse(svg: str, status: int = 200) -> Response:
    """Return an SVG response with the given status code."""
    return Response(
        content=svg,
        media_type="image/svg+xml",
        status_code=status,
        headers={"Cache-Control": "no-cache"}
        )
