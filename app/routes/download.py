from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from database import get_db
from repositories import book_repo

router = APIRouter()

# Formats autorisés (en minuscules)
ALLOWED_FORMATS = {"epub", "mobi", "azw3", "pdf", "txt", "rtf", "lit", "lrf"}

_MIME_TYPES = {
    "epub": "application/epub+zip",
    "mobi": "application/x-mobipocket-ebook",
    "azw3": "application/vnd.amazon.ebook",
    "pdf": "application/pdf",
    "txt": "text/plain",
    "rtf": "application/rtf",
    "lit": "application/x-ms-reader",
    "lrf": "application/x-sony-bbeb",
}


@router.get("/{book_id}/{fmt}")
def download(book_id: int, fmt: str):
    fmt_lower = fmt.lower()

    if fmt_lower not in ALLOWED_FORMATS:
        raise HTTPException(status_code=400, detail=f"Format non supporté : {fmt}")

    with get_db() as conn:
        # Récupère le titre pour le nom de fichier
        book_row = conn.execute(
            "SELECT title FROM books WHERE id = ?", (book_id,)
        ).fetchone()
        if not book_row:
            raise HTTPException(status_code=404, detail="Livre introuvable")

        file_path = book_repo.get_book_file_path(conn, book_id, fmt_lower)

    if not file_path:
        raise HTTPException(
            status_code=404,
            detail=f"Fichier {fmt.upper()} introuvable pour ce livre",
        )

    # Nom de fichier propre pour le téléchargement
    safe_title = "".join(c for c in book_row["title"] if c.isalnum() or c in " -_")[:60]
    filename = f"{safe_title}.{fmt_lower}"

    return FileResponse(
        file_path,
        media_type=_MIME_TYPES.get(fmt_lower, "application/octet-stream"),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
