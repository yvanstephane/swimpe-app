#!/usr/bin/env python3
"""
patch_lisibilite_v3.py — Cartes d'offres : fond et texte toujours assortis.

CONSTAT (capture 2026-07-12) : cartes blanches, titres quasi blancs =
fond et couleur de texte tires de deux mondes differents (aggrave par la
traduction de page Safari qui reecrit le DOM).

CORRECTIF :
  1. Le fond des cartes (expanders) vient de la MEME source que le texte :
     var(--secondary-background-color) + var(--text-color) — un theme,
     une paire coherente, dans les deux modes.
  2. Tous les var(--text-color) recoivent un REPLI (, inherit) : si la
     variable manque, on herite du style Streamlit au lieu d'un rendu
     imprevisible.

Idempotent. Sauvegarde .bak. Syntaxe verifiee.
Usage : python scripts/patch_lisibilite_v3.py [--dry]
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

FIN_V2 = """div[data-testid="stWidgetLabel"] p, div[data-testid="stWidgetLabel"] label {
  font-size:1.12rem !important;}"""
AJOUT_V3 = FIN_V2 + """
/* --- patch_lisibilite_v3 : cartes d'offres, fond et texte assortis --- */
div[data-testid="stExpander"] {
  background: var(--secondary-background-color, transparent);}
div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] details {background: transparent;}
div[data-testid="stExpander"] summary p,
div[data-testid="stExpander"] p,
div[data-testid="stExpander"] li,
div[data-testid="stExpander"] span {
  color: var(--text-color, inherit) !important;}"""


def main() -> None:
    src = P.read_text(encoding="utf-8")
    n = 0
    if "patch_lisibilite_v3" not in src:
        if FIN_V2 not in src:
            print("? ui.py : bloc v2 introuvable — lance d'abord "
                  "patch_lisibilite_v2.py")
            sys.exit(2)
        src = src.replace(FIN_V2, AJOUT_V3, 1); n += 1
    # replis sur toutes les variables texte deja posees (v1/v2)
    if "var(--text-color) !important" in src or "var(--text-color);" in src:
        src = src.replace("var(--text-color) !important",
                          "var(--text-color, inherit) !important")
        src = src.replace("color:var(--text-color);",
                          "color:var(--text-color, inherit);")
        n += 1
    if n == 0:
        print("= ui.py : v3 deja appliquee")
        return
    if DRY:
        print(f"~ ui.py : {n} retouche(s) [DRY-RUN]")
        return
    ast.parse(src)
    bak = P.with_suffix(f".py.bak-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(P, bak)
    P.write_text(src, encoding="utf-8")
    print(f"v ui.py : {n} retouche(s) ({bak.name})")
    print("Relance, puis dans Safari : icone traduction -> Afficher "
          "l'original, et Cmd+R.")


if __name__ == "__main__":
    main()
