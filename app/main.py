from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import settings
from database import test_connection
from routes import authors, books, covers, download, home, search, series, tags

app = FastAPI(
    title="Kobo Calibre Browser",
    description="Interface de navigation Calibre optimisée pour Kobo Clara 2E",
    version="1.0.0",
    docs_url=None,   # Désactiver Swagger UI en prod
    redoc_url=None,
)

# Fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates Jinja2
templates = Jinja2Templates(directory="templates")

# Routers
app.include_router(home.router)
app.include_router(books.router, prefix="/books")
app.include_router(authors.router, prefix="/authors")
app.include_router(tags.router, prefix="/tags")
app.include_router(series.router, prefix="/series")
app.include_router(search.router, prefix="/search")
app.include_router(covers.router, prefix="/covers")
app.include_router(download.router, prefix="/download")


@app.get("/health")
def health_check():
    """Healthcheck pour Docker et Cloudflare Tunnel."""
    db_ok = test_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "error",
        "library_path": str(settings.calibre_library_path),
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "code": 404, "message": "Page introuvable"},
        status_code=404,
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "code": 500, "message": "Erreur serveur"},
        status_code=500,
    )
