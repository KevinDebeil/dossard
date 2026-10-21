#!/usr/bin/env python3
"""Hook PreToolUse : bloque les commandes shell destructrices.

Lit le JSON de Claude Code sur l'entrée standard. Code de sortie 2 (avec un
message sur stderr) pour bloquer, 0 sinon.
"""

import json
import re
import sys

OUTILS = {"Bash", "PowerShell"}
SEPARATEURS = re.compile(r";|&&|\|\||\||&|\n")
SQL = re.compile(r"\bDROP\s+(TABLE|VIEW)\b", re.IGNORECASE)


def _options(jetons: list[str]) -> tuple[set[str], set[str]]:
    """Sépare les options courtes (lettres) et longues d'une liste de jetons."""
    courtes, longues = set(), set()
    for jeton in jetons:
        if jeton.startswith("--"):
            longues.add(jeton.split("=")[0])
        elif jeton.startswith("-") and len(jeton) > 1:
            courtes.update(jeton[1:])
    return courtes, longues


def _raison_segment(jetons: list[str]) -> str | None:
    for i, jeton in enumerate(jetons):
        nom = jeton.replace("\\", "/").rsplit("/", 1)[-1]
        if nom == "rm":
            courtes, longues = _options(jetons[i + 1 :])
            recursif = bool(courtes & {"r", "R"}) or "--recursive" in longues
            force = "f" in courtes or "--force" in longues
            if recursif and force:
                return "rm -rf"
        elif nom == "git" and "push" in jetons[i + 1 :]:
            apres = jetons[jetons.index("push", i) + 1 :]
            courtes, longues = _options(apres)
            if "f" in courtes or "--force" in longues:
                return "git push --force"
    return None


def raison(commande: str) -> str | None:
    for segment in SEPARATEURS.split(commande):
        trouvee = _raison_segment(segment.split())
        if trouvee:
            return trouvee
    correspondance = SQL.search(commande)
    if correspondance:
        return " ".join(correspondance.group(0).upper().split())
    return None


def main() -> int:
    try:
        donnees = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return 0
    if not isinstance(donnees, dict) or donnees.get("tool_name") not in OUTILS:
        return 0
    entree = donnees.get("tool_input")
    commande = entree.get("command") if isinstance(entree, dict) else None
    if not isinstance(commande, str):
        return 0
    motif = raison(commande)
    if motif:
        message = f"Bloqué par le hook garde.py : {motif}\n"
        sys.stderr.buffer.write(message.encode("utf-8"))
        sys.stderr.flush()
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
