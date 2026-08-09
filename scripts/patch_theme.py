#!/usr/bin/env python3
"""
patch_theme.py — Applique l'habillage "destination" dans ui.py.

Ancre CONNUE (vue dans la trace d'erreur de ce matin, ui.py:986) :
    _mode_opp = opportunites_ui.afficher(type_c, destination, code_orig, tr,

On insere juste AVANT :
    import theme_pays
    theme_pays.appliquer(destination, theme_pays.type_interne(type_c), tr)

Effet : CSS global (cartes, boutons, typo aux couleurs du pays) + bandeau
hero officiel ("Travailler au Canada 🇨🇦 — Guichet-Emplois") au-dessus du
contenu. Le thème est choisi par le registre THEMES de theme_pays.py ;
un pays sans thème reçoit le style Yorbity par défaut.

Idempotent. Sauvegarde .bak. Vérifie la syntaxe, restaure si cassé.
Usage : python scripts/patch_theme.py [--dry]
"""
from __future__ import annotations

import ast
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DRY = "--dry" in sys.argv
P = RACINE / "app" / "api" / "ui.py"

ANCRE = re.compile(
    r"^(?P<indent>[ \t]*)_mode_opp = opportunites_ui\.afficher\(", re.M
)

BLOC = (
    "{i}# --- habillage destination (patch_theme.py) ---\n"
    "{i}try:\n"
    "{i}    import theme_pays\n"
    "{i}    theme_pays.appliquer(destination, theme_pays.type_interne(type_c), tr)\n"
    "{i}except Exception as _e_theme:\n"
    "{i}    print('theme_pays indisponible :', _e_theme)\n"
    "{i}# -----------------------------------------------\n"
)


def main() -> None:
    if not P.exists():
        print("ui.py introuvable")
        sys.exit(1)
    src = P.read_text(encoding="utf-8")

    if "theme_pays.appliquer" in src:
        print("= ui.py : theme deja branche")
        return

    m = ANCRE.search(src)
    if not m:
        print("? ui.py : ancre `_mode_opp = opportunites_ui.afficher(` "
              "introuvable — rien ecrit.")
        print("  Verifie : grep -n 'opportunites_ui.afficher' app/api/ui.py")
        sys.exit(2)

    bloc = BLOC.format(i=m.group("indent"))
    nouveau = src[:m.start()] + bloc + src[m.start():]

    if DRY:
        print(f"~ ui.py : insertion du theme avant la ligne "
              f"{src[:m.start()].count(chr(10)) + 1} [DRY-RUN]")
        return

    try:
        ast.parse(nouveau)
    except SyntaxError as e:
        print(f"x syntaxe cassee ligne {e.lineno} — rien ecrit")
        sys.exit(1)

    bak = P.with_suffix(f".py.bak-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(P, bak)
    P.write_text(nouveau, encoding="utf-8")
    print(f"v ui.py : theme branche, syntaxe OK ({bak.name})")
    print("Relance : yorbity")


if __name__ == "__main__":
    main()
