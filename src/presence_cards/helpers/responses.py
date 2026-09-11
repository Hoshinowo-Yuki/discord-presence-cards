from fastapi import Response

_NOT_FOUND_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' width='340' height='120'>"
    "<rect width='340' height='120' rx='12' fill='#2f3136'/>"
    "<text x='24' y='64' fill='#b9bbbe' font-family='sans-serif' font-size='16'>"
    "Presence not found</text></svg>"
)

def notFoundCard() -> Response:
    return Response(content=_NOT_FOUND_SVG, media_type="image/svg+xml", status_code=404)

def svgResponse(svg: str, status: int = 200) -> Response:
    return Response(content=svg, media_type="image/svg+xml", status_code=status,
                    headers={"Cache-Control": "no-cache"})