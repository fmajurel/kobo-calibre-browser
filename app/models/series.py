from pydantic import BaseModel


class Series(BaseModel):
    id: int
    name: str
    sort: str
    book_count: int = 0
