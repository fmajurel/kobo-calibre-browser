import sqlite3
from models.author import Author


def get_all_authors(conn: sqlite3.Connection) -> list[Author]:
    """Retourne tous les auteurs triés, avec le nombre de livres."""
    rows = conn.execute(
        """
        SELECT a.id, a.name, a.sort, COUNT(bal.book) AS book_count
        FROM authors a
        LEFT JOIN books_authors_link bal ON bal.author = a.id
        GROUP BY a.id
        ORDER BY a.sort
        """
    ).fetchall()
    return [
        Author(id=r["id"], name=r["name"], sort=r["sort"], book_count=r["book_count"])
        for r in rows
    ]


def get_author_by_id(conn: sqlite3.Connection, author_id: int) -> Author | None:
    row = conn.execute(
        """
        SELECT a.id, a.name, a.sort, COUNT(bal.book) AS book_count
        FROM authors a
        LEFT JOIN books_authors_link bal ON bal.author = a.id
        WHERE a.id = ?
        GROUP BY a.id
        """,
        (author_id,),
    ).fetchone()
    if not row:
        return None
    return Author(id=row["id"], name=row["name"], sort=row["sort"], book_count=row["book_count"])
