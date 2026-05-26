from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import settings
from database import get_db
from repositories import book_repo, tag_repo

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def tag_list(request: Request):
    with get_db() as conn:
        tags = tag_repo.get_all_tags(conn)

    return templates.TemplateResponse(
        "tag_list.html",
        {
            "request": request,
            "tags": tags,
            "breadcrumbs": [("Genres", "/tags")],
        },
    )


@router.get("/{tag_id}", response_class=HTMLResponse)
def tag_detail(request: Request, tag_id: int, page: int = 1):
    with get_db() as conn:
        tag = tag_repo.get_tag_by_id(conn, tag_id)
        if not tag:
            raise HTTPException(status_code=404, detail="Genre introuvable")
        result = book_repo.get_books_by_tag(
            conn, tag_id, page=page, per_page=settings.items_per_page
        )

    return templates.TemplateResponse(
        "book_list.html",
        {
            "request": request,
            "page_obj": result,
            "title": tag.name,
            "breadcrumbs": [
                ("Genres", "/tags"),
                (tag.name, f"/tags/{tag_id}"),
            ],
            "base_url": f"/tags/{tag_id}",
        },
    )
