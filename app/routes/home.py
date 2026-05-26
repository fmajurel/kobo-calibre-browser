from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        recent = conn.execute(
            """
            SELECT id, title, has_cover
            FROM books
            ORDER BY timestamp DESC
            LIMIT 4
            """
        ).fetchall()

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "total_books": total,
            "recent_books": recent,
            "breadcrumbs": [],
        },
    )
