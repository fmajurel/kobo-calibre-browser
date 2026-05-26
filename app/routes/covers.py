from pathlib import Path

from fastapi import APIRouter, Response
from fastapi.responses import FileResponse

from database import get_db
from repositories import book_repo

router = APIRouter()

_PLACEHOLDER = Path("static/img/no-cover.svg")
_CACHE_HEADER = "public, max-age=3600"


@router.get("/{book_id}")
def cover(book_id: int):
    with get_db() as conn:
        cover_path = book_repo.get_book_cover_path(conn, book_id)

    if cover_path:
        return FileResponse(
            cover_path,
            media_type="image/jpeg",
            headers={"Cache-Control": _CACHE_HEADER},
        )

    # Fallback : image placeholder
    if _PLACEHOLDER.exists():
        return FileResponse(
            _PLACEHOLDER,
            media_type="image/png",
            headers={"Cache-Control": _CACHE_HEADER},
        )

    return Response(status_code=204)
