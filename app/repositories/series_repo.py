import sqlite3
from models.series import Series


def get_all_series(conn: sqlite3.Connection) -> list[Series]:
    """Retourne toutes les séries triées, avec le nombre de livres."""
    rows = conn.execute(
        """
        SELECT s.id, s.name, s.sort, COUNT(bsl.book) AS book_count
        FROM series s
        LEFT JOIN books_series_link bsl ON bsl.series = s.id
        GROUP BY s.id
        ORDER BY s.sort
        """
    ).fetchall()
    return [
        Series(id=r["id"], name=r["name"], sort=r["sort"], book_count=r["book_count"])
        for r in rows
    ]


def get_series_by_id(conn: sqlite3.Connection, series_id: int) -> Series | None:
    row = conn.execute(
        """
        SELECT s.id, s.name, s.sort, COUNT(bsl.book) AS book_count
        FROM series s
        LEFT JOIN books_series_link bsl ON bsl.series = s.id
        WHERE s.id = ?
        GROUP BY s.id
        """,
        (series_id,),
    ).fetchone()
    if not row:
        return None
    return Series(id=row["id"], name=row["name"], sort=row["sort"], book_count=row["book_count"])
