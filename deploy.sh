#!/bin/bash
# =============================================================================
# deploy.sh — Mise à jour Kobo Calibre Browser sur Unraid
# Usage : bash deploy.sh
# =============================================================================

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
APPDATA_DIR="/mnt/user/appdata/kobo-calibre-browser"
REPO_URL="https://github.com/fmajurel/kobo-calibre-browser"
COMPOSE_FILE="$APPDATA_DIR/docker-compose.yml"

# ── Couleurs ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${GREEN}[✓]${NC} $*"; }
warning() { echo -e "${YELLOW}[!]${NC} $*"; }
error()   { echo -e "${RED}[✗]${NC} $*"; exit 1; }

echo ""
echo "══════════════════════════════════════════"
echo "  Déploiement Kobo Calibre Browser"
echo "══════════════════════════════════════════"
echo ""

# ── 1. Mettre à jour les sources ───────────────────────────────────────────────
if git -C "$APPDATA_DIR" rev-parse --git-dir &>/dev/null; then
    # Le dossier appdata EST un dépôt git → simple pull
    info "Dépôt git détecté dans $APPDATA_DIR"
    info "Récupération des derniers commits..."
    git -C "$APPDATA_DIR" pull --ff-only
else
    # Pas de git dans appdata → clone dans un dossier temporaire puis copie
    warning "Pas de dépôt git dans $APPDATA_DIR, clonage depuis GitHub..."
    TMP_DIR=$(mktemp -d)
    trap 'rm -rf "$TMP_DIR"' EXIT

    git clone --depth 1 "$REPO_URL" "$TMP_DIR/repo"
    info "Clonage terminé."

    # Copier les fichiers de l'application (sans écraser .env ni les données)
    rsync -av --exclude='.env' \
              --exclude='*.db' \
              "$TMP_DIR/repo/" "$APPDATA_DIR/"
    info "Fichiers copiés vers $APPDATA_DIR"
fi

# ── 2. Vérifier que docker-compose.yml est présent ────────────────────────────
[[ -f "$COMPOSE_FILE" ]] || error "docker-compose.yml introuvable dans $APPDATA_DIR"

# ── 3. Rebuild + redémarrage ──────────────────────────────────────────────────
info "Rebuild de l'image Docker (sans cache pour les fichiers Python/HTML)..."
docker compose -f "$COMPOSE_FILE" build --no-cache kobo-calibre

info "Redémarrage du container..."
docker compose -f "$COMPOSE_FILE" up -d --force-recreate kobo-calibre

# ── 4. Vérification santé ─────────────────────────────────────────────────────
info "Attente du démarrage (15 s)..."
sleep 15

STATUS=$(docker inspect --format='{{.State.Health.Status}}' kobo-calibre-browser 2>/dev/null || echo "inconnu")

if [[ "$STATUS" == "healthy" ]]; then
    info "Container healthy ✓"
elif [[ "$STATUS" == "starting" ]]; then
    warning "Container encore en démarrage — vérifier dans quelques secondes :"
    echo "    docker inspect --format='{{.State.Health.Status}}' kobo-calibre-browser"
else
    warning "Statut inattendu : $STATUS"
    echo "    Logs : docker logs kobo-calibre-browser --tail 50"
fi

echo ""
info "Déploiement terminé."
echo ""
