# Kobo Calibre Browser

Interface web de navigation dans une bibliothèque Calibre, optimisée pour la **Kobo Clara 2E** (écran e-ink 6", 1072×1448px). Déployé via Docker sur un serveur **Unraid**, derrière **Traefik** et **Authelia**.

> **Contexte** : Ce projet coexiste avec [calibre-web](https://calibre.domain.fr) (Kobo Sync actif) déjà déployé sur le même serveur. `kobo-calibre-browser` est une interface de **navigation et téléchargement** légère, optimisée pour l'écran e-ink, distincte de calibre-web.

## Architecture

```
[Calibre Desktop] ──écrit──> metadata.db + epub/mobi
                                    │ (volume Docker read-only)
                                    ▼
          [Docker: kobo-calibre FastAPI :8000]
               ├── lit SQLite directement
               ├── Jinja2 SSR + HTMX
               └── FileResponse (covers + downloads)
                                    │
                              Traefik (HTTPS)
                              Authelia (auth)
                                    │
                    https://kobo.domain.fr
                                    │
                       [Kobo Clara 2E — navigateur]
```

## Prérequis

- Serveur Unraid avec Docker
- **Traefik** configuré sur le réseau `docker_network`
- **Authelia** configuré avec file-provider (middleware `authelia@file`)
- Bibliothèque Calibre existante accessible sur le partage Unraid

## Installation

### 1. Cloner le dépôt

```bash
git clone <repo-url> /mnt/user/appdata/kobo-calibre-browser
cd /mnt/user/appdata/kobo-calibre-browser
```

### 2. Configurer l'environnement

```bash
cp .env.example .env
nano .env   # ou vi .env
```

Variables à renseigner :

| Variable | Description | Valeur sur ce serveur |
|----------|-------------|-----------------------|
| `CALIBRE_LIBRARY_PATH` | Chemin absolu de la bibliothèque Calibre sur l'hôte | `/mnt/user/data/media/ebooks/calibre_library` |
| `KOBO_DOMAIN` | Sous-domaine public | `kobo.domain.fr` |
| `TRAEFIK_NETWORK` | Nom du réseau Docker Traefik | `docker_network` |
| `CERT_RESOLVER` | Résolveur TLS dans Traefik | `cloudflare` |
| `AUTHELIA_MIDDLEWARE` | Middleware Authelia | `authelia@file` |

### 3. Lancer

```bash
docker compose up -d --build
```

### 4. Vérifier

```bash
# Santé du container
docker compose ps
docker compose logs -f

# Test direct (depuis le serveur)
curl http://localhost:8000/health
```

### 5. Configurer l'accès dans Authelia

Dans la configuration Authelia (`/mnt/user/appdata/authelia/configuration.yml`), ajouter une règle `access_control` :

```yaml
access_control:
  rules:
    - domain: kobo.domain.fr
      policy: one_factor   # ou two_factor selon ta préférence
```

> **Note** : configurer une durée de session longue dans Authelia (ex: 30 jours) pour ne pas avoir à se ré-authentifier fréquemment depuis la Kobo.

## Utilisation depuis la Kobo

1. Connecter la Kobo au WiFi
2. Ouvrir le navigateur intégré (Menu → Navigateur web)
3. Naviguer vers `https://kobo.domain.fr`
4. S'authentifier via Authelia (une seule fois, cookie valide selon ta config)
5. Parcourir la bibliothèque et télécharger des livres

## Fonctionnalités

- 📖 **Navigation** par auteur, genre, série, date d'ajout
- 🔍 **Recherche** sur titre et auteur
- 📥 **Téléchargement** direct EPUB/MOBI/PDF vers la Kobo
- 🖼️ **Couvertures** des livres avec cache navigateur
- 📱 **UI e-ink** : zéro animation, contraste maximal, zones de tap ≥44px

## Coexistence avec calibre-web

Ce container lit la bibliothèque Calibre **en lecture seule** — il ne modifie jamais `metadata.db`. Il peut donc tourner en parallèle de calibre-web sans aucune interférence :

| | `kobo-calibre-browser` | calibre-web |
|---|---|---|
| URL | `kobo.domain.fr` | `calibre.domain.fr` |
| Accès DB | SQLite read-only | Lecture/écriture |
| Kobo Sync | Non | Oui (OPDS) |
| UI | E-ink optimisé | Interface web complète |

## Mise à jour

```bash
docker compose up -d --build   # rebuild depuis le Dockerfile local
```

## Structure du projet

```
kobo-calibre-browser/
├── docker-compose.yml
├── .env.example
└── app/
    ├── Dockerfile
    ├── main.py              # Point d'entrée FastAPI
    ├── config.py            # Paramètres (Pydantic Settings)
    ├── database.py          # Accès SQLite Calibre (read-only)
    ├── models/              # Modèles Pydantic
    ├── repositories/        # Requêtes SQL
    ├── routes/              # Routes FastAPI
    ├── templates/           # Templates Jinja2
    └── static/              # CSS, JS (HTMX), images
```
