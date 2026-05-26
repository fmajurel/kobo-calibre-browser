import sqlite3
from contextlib import contextmanager
from typing import Generator

from config import settings


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Connexion read-only au SQLite Calibre.
    Une nouvelle connexion est ouverte par requête HTTP.
    SQLite en mode lecture seule est thread-safe.
    """
    db_path = settings.calibre_db_path
    conn = sqlite3.connect(
        f"file:{db_path}?mode=ro",
        uri=True,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row  # Accès par nom de colonne
    try:
        yield conn
    finally:
        conn.close()


def test_connection() -> bool:
    """Vérifie que la base Calibre est accessible."""
    try:
        with get_db() as conn:
            conn.execute("SELECT COUNT(*) FROM books").fetchone()
        return True
    except Exception:
        return False
