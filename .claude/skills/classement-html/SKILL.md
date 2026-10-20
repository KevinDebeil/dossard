---
name: classement-html
description: Génère une page HTML (un fichier .html) du classement d'une épreuve de dossard. À utiliser quand on demande une page, un fichier HTML ou une version imprimable/partageable du classement d'une épreuve.
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/scripts/classement_html.py *)
---

# Page HTML d'un classement

1. **Identifiant de l'épreuve** : s'il n'est pas donné, le chercher dans `data/dossard.db`
   (table `events`, colonnes `id`, `name`, `unit`) en lecture seule, par exemple avec
   `sqlite3` ou le module Python `sqlite3`. S'il y a plusieurs épreuves plausibles,
   demander laquelle à Kevin plutôt que de deviner.
2. **Génération** : depuis la racine du dépôt, lancer exactement :
   `python ${CLAUDE_SKILL_DIR}/scripts/classement_html.py <event_id>`
   Le script importe `fastapi` : il doit tourner avec le Python du venv du dépôt. Si
   `ModuleNotFoundError: No module named 'fastapi'` apparaît, relancer la même commande
   avec `.venv/Scripts` en tête du `PATH` (`PATH="$PWD/.venv/Scripts:$PATH" python ...`).
3. **Ne pas écrire de HTML soi-même** : le script est la seule source de la page.
   S'il échoue (base introuvable, épreuve inconnue, classement indisponible),
   rapporter son message d'erreur tel quel sans contourner.
4. **Réponse** : donner le chemin du fichier produit (`classement-<event_id>.html`, écrit
   dans le répertoire courant) et le nombre d'athlètes classés affiché par le script.
