import sqlite3
from models.tag import Tag


def get_all_tags(conn: sqlite3.Connection) -> list[Tag]:
    """Retourne tous les genres/tags triés, avec le nombre de livres."""
    rows = conn.execute(
        """
        SELECT t.id, t.name, COUNT(btl.book) AS book_count
        FROM tags t
        LEFT JOIN books_tags_link btl ON btl.tag = t.id
        GROUP BY t.id
        ORDER BY t.name
        """
    ).fetchall()
    return [
        Tag(id=r["id"], name=r["name"], book_count=r["book_count"])
        for r in rows
    ]


def get_tag_by_id(conn: sqlite3.Connection, tag_id: int) -> Tag | None:
    row = conn.execute(
        """
        SELECT t.id, t.name, COUNT(btl.book) AS book_count
        FROM tags t
        LEFT JOIN books_tags_link btl ON btl.tag = t.id
        WHERE t.id = ?
        GROUP BY t.id
        """,
        (tag_id,),
    ).fetchone()
    if not row:
        return None
    return Tag(id=row["id"], name=row["name"], book_count=row["book_count"])
