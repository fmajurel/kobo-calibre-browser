from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import settings
from database import get_db
from repositories import book_repo

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def search(request: Request, q: str = "", page: int = 1):
    results = None
    if q.strip():
        with get_db() as conn:
            results = book_repo.search_books(
                conn, q.strip(), page=page, per_page=settings.items_per_page
            )

    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "q": q,
            "page_obj": results,
            "breadcrumbs": [("Recherche", "/search")],
            "base_url": f"/search?q={q}&",
        },
    )
