from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import settings
from database import get_db
from repositories import book_repo

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def book_list(request: Request, page: int = 1):
    with get_db() as conn:
        result = book_repo.get_books_paginated(conn, page=page, per_page=settings.items_per_page)

    return templates.TemplateResponse(
        "book_list.html",
        {
            "request": request,
            "page_obj": result,
            "title": "Tous les livres",
            "breadcrumbs": [("Livres", "/books")],
            "base_url": "/books",
        },
    )


@router.get("/{book_id}", response_class=HTMLResponse)
def book_detail(request: Request, book_id: int):
    with get_db() as conn:
        book = book_repo.get_book_by_id(conn, book_id)

    if not book:
        raise HTTPException(status_code=404, detail="Livre introuvable")

    return templates.TemplateResponse(
        "book_detail.html",
        {
            "request": request,
            "book": book,
            "breadcrumbs": [("Livres", "/books"), (book.title, f"/books/{book_id}")],
        },
    )
