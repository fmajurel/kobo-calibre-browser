from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from database import get_db
from repositories import book_repo

router = APIRouter(prefix="/api")

SortField = Literal["title", "timestamp", "author"]
SortOrder = Literal["asc", "desc"]


@router.get("/books")
def api_books(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort: SortField = "timestamp",
    order: SortOrder = "desc",
):
    with get_db() as conn:
        return book_repo.get_books_paginated(conn, page, per_page, sort, order)


@router.get("/books/{book_id}")
def api_book_detail(book_id: int):
    with get_db() as conn:
        book = book_repo.get_book_by_id(conn, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Livre introuvable")
    return book


@router.get("/search")
def api_search(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort: SortField = "title",
    order: SortOrder = "asc",
):
    with get_db() as conn:
        return book_repo.search_books(conn, q, page, per_page, sort, order)
