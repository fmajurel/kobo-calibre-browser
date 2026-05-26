from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from database import get_db
from repositories import book_repo, series_repo

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def series_list(request: Request):
    with get_db() as conn:
        all_series = series_repo.get_all_series(conn)

    return templates.TemplateResponse(
        "series_list.html",
        {
            "request": request,
            "series_list": all_series,
            "breadcrumbs": [("Séries", "/series")],
        },
    )


@router.get("/{series_id}", response_class=HTMLResponse)
def series_detail(request: Request, series_id: int):
    with get_db() as conn:
        s = series_repo.get_series_by_id(conn, series_id)
        if not s:
            raise HTTPException(status_code=404, detail="Série introuvable")
        books = book_repo.get_books_by_series(conn, series_id)

    return templates.TemplateResponse(
        "series_detail.html",
        {
            "request": request,
            "series": s,
            "books": books,
            "breadcrumbs": [
                ("Séries", "/series"),
                (s.name, f"/series/{series_id}"),
            ],
        },
    )
