from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import settings
from database import get_db
from repositories import author_repo, book_repo

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def author_list(request: Request):
    with get_db() as conn:
        authors = author_repo.get_all_authors(conn)

    return templates.TemplateResponse(
        "author_list.html",
        {
            "request": request,
            "authors": authors,
            "breadcrumbs": [("Auteurs", "/authors")],
        },
    )


@router.get("/{author_id}", response_class=HTMLResponse)
def author_detail(request: Request, author_id: int, page: int = 1):
    with get_db() as conn:
        author = author_repo.get_author_by_id(conn, author_id)
        if not author:
            raise HTTPException(status_code=404, detail="Auteur introuvable")
        result = book_repo.get_books_by_author(
            conn, author_id, page=page, per_page=settings.items_per_page
        )

    return templates.TemplateResponse(
        "book_list.html",
        {
            "request": request,
            "page_obj": result,
            "title": author.name,
            "breadcrumbs": [
                ("Auteurs", "/authors"),
                (author.name, f"/authors/{author_id}"),
            ],
            "base_url": f"/authors/{author_id}",
        },
    )
