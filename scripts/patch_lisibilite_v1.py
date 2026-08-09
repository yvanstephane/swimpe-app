#!/usr/bin/env python3
"""
patch_lisibilite_v1.py — Police plus lisible + vrai support du mode nuit.

CONSTAT (css.txt du 2026-07-12) :
  - Libelles et menus deroulants (Type de projet, Pays...) : taille par
    defaut Streamlit (~0.88 rem), trop petite.
  - Couleurs figees pour le mode clair : tagline #6b7280 (illisible sur
    fond sombre), bordure d'expander #e5e7eb, badge bleu clair fige.

CORRECTIF :
  1. Libelles de champs, valeurs et options des menus, titres des cartes
     d'offres -> ~1.05 rem, gras leger.
  2. Toutes les couleurs de texte via var(--text-color) (+ opacite pour
     les nuances) : elles suivent le basculement clair/sombre du theme.
  3. Badge et bordures en teintes translucides, correctes sur les deux fonds.

Idempotent. Sauvegarde .bak. Syntaxe verifiee, restauration si casse.
Usage : python scripts/patch_lisibilite_v1.py [--dry]
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

# --- 1. badge : teintes translucides liees au theme -------------------------
A_BADGE = """.badge {display:inline-block; background:#eff6ff; color:#1d4ed8; border-radius:999px;
  padding:.15rem .7rem; font-size:.8rem; margin-right:.4rem;}"""
R_BADGE = """.badge {display:inline-block; background:rgba(59,130,246,.16);
  color:var(--text-color); border:1px solid rgba(59,130,246,.4); border-radius:999px;
  padding:.18rem .75rem; font-size:.88rem; margin-right:.4rem;}"""

# --- 2. expander + regles de lisibilite (ajoutees au meme bloc <style>) -----
A_EXP = """div[data-testid="stExpander"] {border-radius:12px; border:1px solid #e5e7eb; margin-bottom:.4rem;}"""
R_EXP = """div[data-testid="stExpander"] {border-radius:12px;
  border:1px solid rgba(128,128,128,.35); margin-bottom:.4rem;}
/* --- Lisibilite (patch_lisibilite) : tailles + couleurs liees au theme --- */
div[data-testid="stWidgetLabel"] p, div[data-testid="stWidgetLabel"] label {
  font-size:1.06rem !important; font-weight:600;
  color:var(--text-color) !important;}
div[data-baseweb="select"] div {font-size:1.04rem !important;}
li[role="option"], ul[data-testid="stSelectboxVirtualDropdown"] li {
  font-size:1.04rem !important;}
div[data-testid="stExpander"] summary p {
  font-size:1.06rem !important; font-weight:600;
  color:var(--text-color) !important;}
div[data-testid="stExpander"] p, div[data-testid="stExpander"] li {
  font-size:1.0rem; color:var(--text-color);}
div[data-testid="stCaptionContainer"] p {font-size:.95rem !important;
  color:var(--text-color) !important; opacity:.8;}
div[data-testid="stMarkdownContainer"] p {color:var(--text-color);}"""

# --- 3. tagline : gris fige -> couleur du theme ------------------------------
A_TAG = """<p style='color:#6b7280; margin-top:.15rem; font-size:1.05rem;'>"""
R_TAG = """<p style='color:var(--text-color); opacity:.72; margin-top:.15rem; font-size:1.1rem;'>"""


def main() -> None:
    src = P.read_text(encoding="utf-8")
    if "patch_lisibilite" in src:
        print("= ui.py : lisibilite deja patchee")
        return
    n = 0
    for a, r in ((A_BADGE, R_BADGE), (A_EXP, R_EXP), (A_TAG, R_TAG)):
        if a in src:
            src = src.replace(a, r, 1); n += 1
        else:
            print(f"? ancre absente : {a[:52]!r}…")
    if n != 3:
        print(f"? {n}/3 retouches seulement — RIEN ecrit")
        sys.exit(2)
    if DRY:
        print("~ ui.py : 3 retouches [DRY-RUN]")
        return
    ast.parse(src)
    bak = P.with_suffix(f".py.bak-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(P, bak)
    P.write_text(src, encoding="utf-8")
    print(f"v ui.py : 3 retouches ({bak.name})")
    print("Relance puis recharge le navigateur (Cmd+R).")


if __name__ == "__main__":
    main()
