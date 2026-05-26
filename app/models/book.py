from datetime import datetime
from pydantic import BaseModel

from models.author import Author
from models.series import Series
from models.tag import Tag


class BookFormat(BaseModel):
    format: str           # "EPUB", "MOBI", "PDF"
    size_bytes: int
    name: str             # Nom du fichier sans extension


class BookListItem(BaseModel):
    id: int
    title: str
    sort: str
    authors: list[Author] = []
    has_cover: bool
    formats: list[str] = []     # ["EPUB", "MOBI"]
    series: Series | None = None
    series_index: float | None = None


class BookDetail(BookListItem):
    pubdate: datetime | None = None
    timestamp: datetime | None = None
    isbn: str | None = None
    tags: list[Tag] = []
    comment: str | None = None       # HTML depuis Calibre
    rating: int | None = None        # 0–10 en base, affiché /2 = nb étoiles
    publisher: str | None = None
    formats: list[BookFormat] = []   # Avec taille de fichier
