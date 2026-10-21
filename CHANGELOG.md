# Changelog

## Non publié

- Correction : `GET /competitions/{competition_id}/results.csv` échappe désormais correctement les champs contenant une virgule, un guillemet ou un saut de ligne (ex. nom de club), qui décalaient les colonnes.
- Changement : `GET /events/{event_id}/ranking` renvoie désormais la liste nue des entrées (plus d'enveloppe `{"data", "count"}`) ; 404 au format `{"error": {...}}` si l'épreuve est introuvable. Les routes de `results` portent un `summary` en français.
- Ajout de la pagination à `GET /athletes` : `?limit=` (1 à 100, défaut 50) et `?offset=` (≥ 0, défaut 0), appliquées après le filtre `?club=`. Valeur hors bornes : 422.
- Ajout de `GET /athletes/{athlete_id}` : détail d'un athlète (404 si introuvable).
