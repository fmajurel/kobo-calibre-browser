from pydantic import BaseModel


class Tag(BaseModel):
    id: int
    name: str
    book_count: int = 0
