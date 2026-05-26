from pydantic import BaseModel


class Author(BaseModel):
    id: int
    name: str
    sort: str

    # Nombre de livres (optionnel, rempli dans les listes)
    book_count: int = 0
