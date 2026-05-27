from urllib.parse import quote

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from config import settings
from database import test_connection
from routes import authors, books, covers, download, home, search, series, tags

app = FastAPI(
    title="Kobo Calibre Browser",
    description="Interface de navigation Calibre optimisée pour Kobo Clara 2E",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)

# Fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates Jinja2
templates = Jinja2Templates(directory="templates")


# ── Middleware d'authentification ────────────────────────────────────────────
# Doit être défini AVANT l'ajout de SessionMiddleware ci-dessous
# (SessionMiddleware est ajouté après → devient la couche externe → s'exécute en premier)

@app.middleware("http")
async def require_auth(request: Request, call_next):
    path = request.url.path
    # Chemins publics : login, health, fichiers statiques
    if path == "/login" or path == "/health" or path.startswith("/static/"):
        return await call_next(request)
    # Vérifier la session
    if not request.session.get("authenticated"):
        next_url = quote(str(request.url), safe="")
        return RedirectResponse(f"/login?next={next_url}", status_code=302)
    return await call_next(request)


# SessionMiddleware ajouté en dernier → couche externe → s'exécute avant require_auth
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    max_age=30 * 24 * 3600,   # 30 jours
    https_only=True,           # Cookie Secure (HTTPS uniquement)
    same_site="lax",
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(home.router)
app.include_router(books.router, prefix="/books")
app.include_router(authors.router, prefix="/authors")
app.include_router(tags.router, prefix="/tags")
app.include_router(series.router, prefix="/series")
app.include_router(search.router, prefix="/search")
app.include_router(covers.router, prefix="/covers")
app.include_router(download.router, prefix="/download")


# ── Routes de login / logout ─────────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request, next: str = "/", error: str = ""):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "next": next, "error": error},
    )


@app.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    password: str = Form(...),
    next: str = Form("/"),
):
    if settings.app_password and password == settings.app_password:
        request.session["authenticated"] = True
        # Utiliser location.replace() pour ne pas ajouter /login à l'historique
        safe_next = next if next.startswith("/") else "/"
        return HTMLResponse(f'<script>location.replace("{safe_next}")</script>')
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "next": next, "error": "Mot de passe incorrect"},
        status_code=401,
    )


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)


# ── Healthcheck ───────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    db_ok = test_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "error",
        "library_path": str(settings.calibre_library_path),
    }


# ── Gestionnaires d'erreurs ───────────────────────────────────────────────────

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