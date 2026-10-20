# Changelog

## Non publié

- Ajout de la pagination à `GET /athletes` : `?limit=` (1 à 100, défaut 50) et `?offset=` (≥ 0, défaut 0), appliquées après le filtre `?club=`. Valeur hors bornes : 422.
- Ajout de `GET /athletes/{athlete_id}` : détail d'un athlète (404 si introuvable).
