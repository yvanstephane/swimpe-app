#!/usr/bin/env python3
"""
patch_lisibilite_v4.py — Couleurs rendues au theme natif ; on garde les tailles.

DIAGNOSTIC (deux captures 2026-07-12) : en clair tout est coherent ; en
sombre le texte suit le theme mais --secondary-background-color reste
figee claire -> cartes blanches, texte clair, illisible. Les variables de
theme ne sont pas fiables sur cette version de Streamlit.

CORRECTIF : plus AUCUNE couleur imposee par nos règles — background
transparent (rendu natif, qui etait correct dans les deux modes avant nos
patchs) et color:inherit partout. Ne restent que les acquis demandes :
tailles des libelles, menus, titres de cartes, badge translucide.

Idempotent. Sauvegarde .bak. Syntaxe verifiee.
Usage : python scripts/patch_lisibilite_v4.py [--dry]
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


def main() -> None:
    src = P.read_text(encoding="utf-8")
    if "patch_lisibilite_v4" in src:
        print("= ui.py : v4 deja appliquee")
        return
    if "patch_lisibilite_v3" not in src:
        print("? ui.py : v3 absente — lance d'abord patch_lisibilite_v3.py")
        sys.exit(2)
    n = 0
    # 1. fond des cartes : rendu natif du theme
    a1 = "background: var(--secondary-background-color, transparent);"
    if a1 in src:
        src = src.replace(a1, "background: transparent;  /* patch_lisibilite_v4 */")
        n += 1
    # 2. plus aucune couleur imposee : inherit partout ou nous avions des var()
    for a in ("var(--text-color, inherit)", "var(--text-color)"):
        if a in src:
            src = src.replace(a, "inherit")
            n += 1
    if n == 0:
        print("? ui.py : aucune ancre trouvee — rien ecrit")
        sys.exit(2)
    if DRY:
        print(f"~ ui.py : {n} famille(s) de retouches [DRY-RUN]")
        return
    ast.parse(src)
    bak = P.with_suffix(f".py.bak-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(P, bak)
    P.write_text(src, encoding="utf-8")
    print(f"v ui.py : couleurs rendues au theme natif, tailles conservees ({bak.name})")
    print("Relance puis Cmd+R — teste les DEUX modes.")


if __name__ == "__main__":
    main()
