#!/usr/bin/env python3
"""
patch_lisibilite_v5.py — Les boites blanches, de force.

CONSTAT : meme rendues "transparentes" par la v4, les cartes restent
blanches en mode nuit — Streamlit repeint leur fond avec des regles plus
specifiques que les notres. Sans !important, nous perdons l'arbitrage CSS.

CORRECTIF : transparence IMPOSEE (!important) sur toutes les couches de
la carte (expander, details, summary, conteneurs internes). Le fond des
cartes devient celui de la page — sombre en mode nuit, clair en mode
jour — et le texte herite de la couleur de page, toujours assortie.
La bordure conserve la delimitation des cartes.

Idempotent. Sauvegarde .bak. Syntaxe verifiee.
Usage : python scripts/patch_lisibilite_v5.py [--dry]
"""
from __future__ import annotations

import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DRY = "--dry" in sys.argv
P = RACINE / "app" / "api" / "ui.py"

ANCRE = "background: transparent;  /* patch_lisibilite_v4 */"
REMPLACE = """background: transparent !important;
  background-color: transparent !important;}
/* patch_lisibilite_v5 : transparence imposee sur TOUTES les couches */
div[data-testid="stExpander"] details,
div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] summary > div,
div[data-testid="stExpander"] > details > div,
div[data-testid="stExpanderDetails"] {
  background: transparent !important;
  background-color: transparent !important;
  color: inherit !important;"""


def main() -> None:
    src = P.read_text(encoding="utf-8")
    if "patch_lisibilite_v5" in src:
        print("= ui.py : v5 deja appliquee")
        return
    if ANCRE not in src:
        print("? ui.py : marqueur v4 introuvable — lance d'abord "
              "patch_lisibilite_v4.py")
        sys.exit(2)
    if DRY:
        print("~ ui.py : 1 retouche [DRY-RUN]")
        return
    nouveau = src.replace(ANCRE, REMPLACE, 1)
    ast.parse(nouveau)
    bak = P.with_suffix(f".py.bak-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(P, bak)
    P.write_text(nouveau, encoding="utf-8")
    print(f"v ui.py : transparence imposee ({bak.name})")
    print("Relance puis Cmd+R — teste les DEUX modes.")


if __name__ == "__main__":
    main()
