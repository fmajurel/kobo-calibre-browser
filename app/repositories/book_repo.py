"""
Requêtes SQL sur la base Calibre pour les livres.
Toutes les requêtes sont en lecture seule.
"""
import sqlite3
from datetime import datetime
from pathlib import Path

from config import settings
from models.author import Author
from models.book import BookDetail, BookFormat, BookListItem
from models.pagination import Page, PaginationMeta
from models.series import Series
from models.tag import Tag


def _parse_calibre_date(value: str | None) -> datetime | None:
    """
    Parse une date Calibre (ISO 8601) en datetime.
    Retourne None pour les valeurs manquantes ou les dates sentinelles
    (ex: "0101-01-01 00:00:00+00:00" = "pas de date connue" dans Calibre).
    """
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value))
        # Calibre utilise l'an 101 comme valeur sentinelle "pas de date"
        if dt.year < 1000:
            return None
        return dt
    except (ValueError, TypeError):
        return None


# ─── Helpers — fiche détaillée (1 livre) ──────────────────────────────────────

def _get_authors(conn: sqlite3.Connection, book_id: int) -> list[Author]:
    rows = conn.execute(
        """
        SELECT a.id, a.name, a.sort
        FROM authors a
        JOIN books_authors_link bal ON bal.author = a.id
        WHERE bal.book = ?
        ORDER BY a.sort
        """,
        (book_id,),
    ).fetchall()
    return [Author(id=r["id"], name=r["name"], sort=r["sort"]) for r in rows]


def _get_formats_detail(conn: sqlite3.Connection, book_id: int) -> list[BookFormat]:
    rows = conn.execute(
        "SELECT format, uncompressed_size, name FROM data WHERE book = ? ORDER BY format",
        (book_id,),
    ).fetchall()
    return [
        BookFormat(format=r["format"], size_bytes=r["uncompressed_size"], name=r["name"])
        for r in rows
    ]


def _get_series(conn: sqlite3.Connection, book_id: int) -> Series | None:
    row = conn.execute(
        """
        SELECT s.id, s.name, s.sort
        FROM series s
        JOIN books_series_link bsl ON bsl.series = s.id
        WHERE bsl.book = ?
        """,
        (book_id,),
    ).fetchone()
    if row:
        return Series(id=row["id"], name=row["name"], sort=row["sort"])
    return None


# ─── Helpers — listes (N livres, sans N+1) ────────────────────────────────────

def _get_authors_batch(
    conn: sqlite3.Connection, book_ids: list[int]
) -> dict[int, list[Author]]:
    """Charge tous les auteurs pour une liste de livres en une seule requête."""
    result: dict[int, list[Author]] = {bid: [] for bid in book_ids}
    if not book_ids:
        return result
    ph = ",".join("?" * len(book_ids))
    rows = conn.execute(
        f"""
        SELECT bal.book, a.id, a.name, a.sort
        FROM authors a
        JOIN books_authors_link bal ON bal.author = a.id
        WHERE bal.book IN ({ph})
        ORDER BY a.sort
        """,
        book_ids,
    ).fetchall()
    for r in rows:
        result[r["book"]].append(Author(id=r["id"], name=r["name"], sort=r["sort"]))
    return result


def _get_formats_list_batch(
    conn: sqlite3.Connection, book_ids: list[int]
) -> dict[int, list[str]]:
    """Charge tous les formats (noms) pour une liste de livres en une seule requête."""
    result: dict[int, list[str]] = {bid: [] for bid in book_ids}
    if not book_ids:
        return result
    ph = ",".join("?" * len(book_ids))
    rows = conn.execute(
        f"SELECT book, format FROM data WHERE book IN ({ph}) ORDER BY format",
        book_ids,
    ).fetchall()
    for r in rows:
        result[r["book"]].append(r["format"])
    return result


def _get_series_batch(
    conn: sqlite3.Connection, book_ids: list[int]
) -> dict[int, Series]:
    """Charge toutes les séries pour une liste de livres en une seule requête."""
    if not book_ids:
        return {}
    ph = ",".join("?" * len(book_ids))
    rows = conn.execute(
        f"""
        SELECT bsl.book, s.id, s.name, s.sort
        FROM series s
        JOIN books_series_link bsl ON bsl.series = s.id
        WHERE bsl.book IN ({ph})
        """,
        book_ids,
    ).fetchall()
    return {r["book"]: Series(id=r["id"], name=r["name"], sort=r["sort"]) for r in rows}


def _rows_to_list_items(
    conn: sqlite3.Connection, rows: list[sqlite3.Row]
) -> list[BookListItem]:
    """
    Convertit une liste de lignes books en BookListItem.
    Utilise 3 requêtes batch (IN) au lieu de 3×N requêtes individuelles.
    """
    if not rows:
        return []
    book_ids = [r["id"] for r in rows]
    authors_map  = _get_authors_batch(conn, book_ids)
    formats_map  = _get_formats_list_batch(conn, book_ids)
    series_map   = _get_series_batch(conn, book_ids)

    items = []
    for row in rows:
        bid    = row["id"]
        series = series_map.get(bid)
        items.append(BookListItem(
            id=bid,
            title=row["title"],
            sort=row["sort"],
            authors=authors_map.get(bid, []),
            has_cover=bool(row["has_cover"]),
            formats=formats_map.get(bid, []),
            series=series,
            series_index=row["series_index"] if series else None,
        ))
    return items


# ─── Requêtes principales ─────────────────────────────────────────────────────

def get_books_paginated(
    conn: sqlite3.Connection,
    page: int = 1,
    per_page: int = 20,
    sort: str = "timestamp",
    order: str = "desc",
) -> Page[BookListItem]:
    offset = (page - 1) * per_page
    dir_ = "ASC" if order == "asc" else "DESC"
    total = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]

    if sort == "author":
        rows = conn.execute(
            f"""
            SELECT b.id, b.title, b.sort, b.has_cover, b.series_index
            FROM books b
            LEFT JOIN (
                SELECT bal.book, MIN(a.sort) AS author_sort
                FROM books_authors_link bal
                JOIN authors a ON a.id = bal.author
                GROUP BY bal.book
            ) aa ON aa.book = b.id
            ORDER BY COALESCE(aa.author_sort, '') {dir_}, b.sort ASC
            LIMIT ? OFFSET ?
            """,
            (per_page, offset),
        ).fetchall()
    else:
        col = "sort" if sort == "title" else "timestamp"
        rows = conn.execute(
            f"""
            SELECT id, title, sort, has_cover, series_index
            FROM books
            ORDER BY {col} {dir_}
            LIMIT ? OFFSET ?
            """,
            (per_page, offset),
        ).fetchall()

    return Page(
        items=_rows_to_list_items(conn, rows),
        meta=PaginationMeta(page=page, per_page=per_page, total=total),
    )


def get_book_by_id(conn: sqlite3.Connection, book_id: int) -> BookDetail | None:
    row = conn.execute(
        """
        SELECT id, title, sort, has_cover, series_index,
               pubdate, timestamp
        FROM books
        WHERE id = ?
        """,
        (book_id,),
    ).fetchone()
    if not row:
        return None

    # Tags
    tag_rows = conn.execute(
        """
        SELECT t.id, t.name
        FROM tags t
        JOIN books_tags_link btl ON btl.tag = t.id
        WHERE btl.book = ?
        ORDER BY t.name
        """,
        (book_id,),
    ).fetchall()
    tags = [Tag(id=r["id"], name=r["name"]) for r in tag_rows]

    # Résumé (commentaire HTML)
    comment_row = conn.execute(
        "SELECT text FROM comments WHERE book = ?", (book_id,)
    ).fetchone()
    comment = comment_row["text"] if comment_row else None

    # Note (0–10)
    rating_row = conn.execute(
        """
        SELECT r.rating
        FROM ratings r
        JOIN books_ratings_link brl ON brl.rating = r.id
        WHERE brl.book = ?
        """,
        (book_id,),
    ).fetchone()
    rating = rating_row["rating"] if rating_row else None

    # Éditeur
    pub_row = conn.execute(
        """
        SELECT p.name
        FROM publishers p
        JOIN books_publishers_link bpl ON bpl.publisher = p.id
        WHERE bpl.book = ?
        """,
        (book_id,),
    ).fetchone()
    publisher = pub_row["name"] if pub_row else None

    series = _get_series(conn, book_id)

    return BookDetail(
        id=row["id"],
        title=row["title"],
        sort=row["sort"],
        authors=_get_authors(conn, book_id),
        has_cover=bool(row["has_cover"]),
        formats=_get_formats_detail(conn, book_id),
        series=series,
        series_index=row["series_index"] if series else None,
        pubdate=_parse_calibre_date(row["pubdate"]),
        timestamp=_parse_calibre_date(row["timestamp"]),
        tags=tags,
        comment=comment,
        rating=rating,
        publisher=publisher,
    )


def get_book_file_path(conn: sqlite3.Connection, book_id: int, fmt: str) -> Path | None:
    """
    Retourne le chemin absolu du fichier epub/mobi pour un livre donné.
    Valide que le format est bien déclaré en base (sécurité anti path traversal).
    """
    fmt_upper = fmt.upper()

    # Vérifier que le format existe pour ce livre
    data_row = conn.execute(
        "SELECT name FROM data WHERE book = ? AND format = ?",
        (book_id, fmt_upper),
    ).fetchone()
    if not data_row:
        return None

    # Récupérer le chemin relatif du livre
    book_row = conn.execute("SELECT path FROM books WHERE id = ?", (book_id,)).fetchone()
    if not book_row:
        return None

    # Construire le chemin absolu
    library = settings.calibre_library_path
    base = library / book_row["path"] / data_row["name"]
    if fmt_upper == "KEPUB":
        # Calibre stocke les fichiers KEPUB avec l'extension simple .kepub
        file_path = base.parent / (base.name + ".kepub")
    else:
        file_path = base.with_suffix(f".{fmt_upper.lower()}")

    # Vérification anti path traversal
    try:
        file_path.resolve().relative_to(library.resolve())
    except ValueError:
        return None

    return file_path if file_path.exists() else None


def get_book_cover_path(conn: sqlite3.Connection, book_id: int) -> Path | None:
    """Retourne le chemin absolu de cover.jpg, ou None si absent."""
    row = conn.execute(
        "SELECT path, has_cover FROM books WHERE id = ?", (book_id,)
    ).fetchone()
    if not row or not row["has_cover"]:
        return None

    cover_path = settings.calibre_library_path / row["path"] / "cover.jpg"

    # Vérification anti path traversal
    try:
        cover_path.resolve().relative_to(settings.calibre_library_path.resolve())
    except ValueError:
        return None

    return cover_path if cover_path.exists() else None


def search_books(
    conn: sqlite3.Connection,
    query: str,
    page: int = 1,
    per_page: int = 20,
    sort: str = "title",
    order: str = "asc",
) -> Page[BookListItem]:
    """Recherche LIKE sur titre et auteur."""
    like = f"%{query}%"
    offset = (page - 1) * per_page
    dir_ = "ASC" if order == "asc" else "DESC"

    total = conn.execute(
        """
        SELECT COUNT(DISTINCT b.id)
        FROM books b
        LEFT JOIN books_authors_link bal ON bal.book = b.id
        LEFT JOIN authors a ON a.id = bal.author
        WHERE b.title LIKE ? OR a.name LIKE ?
        """,
        (like, like),
    ).fetchone()[0]

    if sort == "author":
        rows = conn.execute(
            f"""
            SELECT DISTINCT b.id, b.title, b.sort, b.has_cover, b.series_index
            FROM books b
            LEFT JOIN books_authors_link bal ON bal.book = b.id
            LEFT JOIN authors a ON a.id = bal.author
            LEFT JOIN (
                SELECT bal2.book, MIN(a2.sort) AS author_sort
                FROM books_authors_link bal2
                JOIN authors a2 ON a2.id = bal2.author
                GROUP BY bal2.book
            ) aa ON aa.book = b.id
            WHERE b.title LIKE ? OR a.name LIKE ?
            ORDER BY COALESCE(aa.author_sort, '') {dir_}, b.sort ASC
            LIMIT ? OFFSET ?
            """,
            (like, like, per_page, offset),
        ).fetchall()
    elif sort == "timestamp":
        rows = conn.execute(
            f"""
            SELECT DISTINCT b.id, b.title, b.sort, b.has_cover, b.series_index
            FROM books b
            LEFT JOIN books_authors_link bal ON bal.book = b.id
            LEFT JOIN authors a ON a.id = bal.author
            WHERE b.title LIKE ? OR a.name LIKE ?
            ORDER BY b.timestamp {dir_}
            LIMIT ? OFFSET ?
            """,
            (like, like, per_page, offset),
        ).fetchall()
    else:
        rows = conn.execute(
            f"""
            SELECT DISTINCT b.id, b.title, b.sort, b.has_cover, b.series_index
            FROM books b
            LEFT JOIN books_authors_link bal ON bal.book = b.id
            LEFT JOIN authors a ON a.id = bal.author
            WHERE b.title LIKE ? OR a.name LIKE ?
            ORDER BY b.sort {dir_}
            LIMIT ? OFFSET ?
            """,
            (like, like, per_page, offset),
        ).fetchall()

    return Page(
        items=_rows_to_list_items(conn, rows),
        meta=PaginationMeta(page=page, per_page=per_page, total=total),
    )


def get_books_by_author(
    conn: sqlite3.Connection,
    author_id: int,
    page: int = 1,
    per_page: int = 20,
) -> Page[BookListItem]:
    offset = (page - 1) * per_page
    total = conn.execute(
        "SELECT COUNT(*) FROM books_authors_link WHERE author = ?", (author_id,)
    ).fetchone()[0]

    rows = conn.execute(
        """
        SELECT b.id, b.title, b.sort, b.has_cover, b.series_index
        FROM books b
        JOIN books_authors_link bal ON bal.book = b.id
        WHERE bal.author = ?
        ORDER BY b.sort
        LIMIT ? OFFSET ?
        """,
        (author_id, per_page, offset),
    ).fetchall()

    return Page(
        items=_rows_to_list_items(conn, rows),
        meta=PaginationMeta(page=page, per_page=per_page, total=total),
    )


def get_books_by_tag(
    conn: sqlite3.Connection,
    tag_id: int,
    page: int = 1,
    per_page: int = 20,
) -> Page[BookListItem]:
    offset = (page - 1) * per_page
    total = conn.execute(
        "SELECT COUNT(*) FROM books_tags_link WHERE tag = ?", (tag_id,)
    ).fetchone()[0]

    rows = conn.execute(
        """
        SELECT b.id, b.title, b.sort, b.has_cover, b.series_index
        FROM books b
        JOIN books_tags_link btl ON btl.book = b.id
        WHERE btl.tag = ?
        ORDER BY b.sort
        LIMIT ? OFFSET ?
        """,
        (tag_id, per_page, offset),
    ).fetchall()

    return Page(
        items=_rows_to_list_items(conn, rows),
        meta=PaginationMeta(page=page, per_page=per_page, total=total),
    )


def get_books_by_series(
    conn: sqlite3.Connection,
    series_id: int,
) -> list[BookListItem]:
    """Retourne tous les livres d'une série, triés par series_index."""
    rows = conn.execute(
        """
        SELECT b.id, b.title, b.sort, b.has_cover, b.series_index
        FROM books b
        JOIN books_series_link bsl ON bsl.book = b.id
        WHERE bsl.series = ?
        ORDER BY b.series_index
        """,
        (series_id,),
    ).fetchall()
    return _rows_to_list_items(conn, rows)
