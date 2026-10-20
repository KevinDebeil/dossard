# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Dossard : API FastAPI + SQLite (`sqlite3`, sans ORM). Code et docs en français.

## Commandes

- Tests : `pytest` (un seul : `pytest tests/test_x.py::test_nom`) ; sous Windows `.\.venv\Scripts\python.exe -m pytest -q`
- Lint + format : `ruff check . && ruff format .`
- Serveur : `uvicorn app.main:app --reload`
- Données d'exemple : `python scripts/seed.py --reset`

## Règles

- Lancer `pytest` avant tout commit : il doit être vert.
- Lancer `ruff check . && ruff format .` après toute modification Python.
- Ne pas ajouter de dépendance sans demander.
- `scripts/legacy/` : lecture seule ; ne rien modifier ni supprimer sans demande explicite.
- Les repositories ne font jamais `commit()` : `get_conn` (`app/db.py`) s'en charge.
- Ne pas exposer de donnée personnelle dans les vues `v_public_*` (lues par `scripts/mcp_dossard.py`).
- Ne jamais lire ni afficher .env : il contient des secrets.

## Erreurs

- Lever une sous-classe d'`ApiError` définie dans `app/errors.py`, jamais `HTTPException`.
- Format de réponse : `{"error": {"code": "...", "message": "..."}}`.

## Tests

- Réutiliser les fixtures de `tests/conftest.py` : `client`, `make_competition`, `make_event`, `make_athlete`, `make_registration`.
- Un fichier de test par router.
- Tester les cas d'erreur 404, 409 et 422 pour chaque route.

## Routes

- Toute route ajoutée ou modifiée : une ligne dans `docs/api.md`.
- Et une entrée en tête de `CHANGELOG.md`, section « Non publié » (créer le fichier s'il n'existe pas).
