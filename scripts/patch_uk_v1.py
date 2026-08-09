#!/usr/bin/env python3
"""
patch_uk_v1.py — Branche l'Angleterre.

  1. sources/registre.py : charge l'adaptateur uk_sponsors
     (Adzuna gb ∩ registre des sponsors Home Office).
  2. theme_pays.py : theme GB (bleu GOV.UK) pour le hero et les pages
     dediees quand la destination est le Royaume-Uni.

Idempotent. Sauvegardes .bak. Syntaxe verifiee, restauration si casse.
Usage : python scripts/patch_uk_v1.py [--dry]
"""
from __future__ import annotations

import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DRY = "--dry" in sys.argv
HORO = datetime.now().strftime("%Y%m%d-%H%M%S")
resultats: list[str] = []


def ecrire(p: Path, contenu: str, n: int) -> None:
    if DRY:
        resultats.append(f"~ {p.name} : {n} retouche(s) [DRY-RUN]")
        return
    bak = p.with_suffix(p.suffix + f".bak-{HORO}")
    shutil.copy2(p, bak)
    p.write_text(contenu, encoding="utf-8")
    try:
        ast.parse(contenu)
    except SyntaxError as e:
        shutil.copy2(bak, p)
        resultats.append(f"x {p.name} : syntaxe cassee l.{e.lineno} — restaure")
        return
    resultats.append(f"v {p.name} : {n} retouche(s) ({bak.name})")


A_REG = """    try:
        from . import mig_de   # noqa: F401
    except Exception as _e:
        log.warning('mig_de non charge : %s', _e)"""
R_REG = A_REG + """
    try:
        from . import uk_sponsors   # noqa: F401
    except Exception as _e:
        log.warning('uk_sponsors non charge : %s', _e)"""


def patch_registre() -> None:
    p = RACINE / "app" / "api" / "sources" / "registre.py"
    src = p.read_text(encoding="utf-8")
    if "uk_sponsors" in src:
        resultats.append("= registre.py : uk_sponsors deja charge")
        return
    if A_REG not in src:
        resultats.append("? registre.py : bloc mig_de introuvable — "
                         "envoie : grep -n 'import' app/api/sources/registre.py")
        return
    ecrire(p, src.replace(A_REG, R_REG, 1), 1)


A_THEME = '    "_defaut": {'
BLOC_GB = '''    "GB": {                                    # patch_uk_v1
        "primaire": "#1d70b8",                 # bleu GOV.UK
        "fonce":    "#0b0c0c",
        "degrade":  "linear-gradient(120deg,#0b0c0c 0%,#1d70b8 100%)",
    },
'''


def patch_theme() -> None:
    p = RACINE / "app" / "api" / "theme_pays.py"
    if not p.exists():
        resultats.append("- theme_pays.py absent (theme GB saute)")
        return
    src = p.read_text(encoding="utf-8")
    if '"GB"' in src:
        resultats.append("= theme_pays.py : GB deja present")
        return
    if A_THEME not in src:
        resultats.append("? theme_pays.py : ancre _defaut introuvable")
        return
    ecrire(p, src.replace(A_THEME, BLOC_GB + A_THEME, 1), 1)


def main() -> None:
    if DRY:
        print(">>> DRY-RUN\n")
    if not (RACINE / "app" / "api" / "sources" / "uk_sponsors.py").exists():
        print("!! sources/uk_sponsors.py manquant — installe-le d'abord.")
        sys.exit(1)
    patch_registre()
    patch_theme()
    print()
    for r in resultats:
        print(" ", r)
    if any(r.startswith("x") for r in resultats):
        sys.exit(1)
    if any(r.startswith("?") for r in resultats):
        sys.exit(2)
    print("\nFINI — telecharge le registre : "
          "python scripts/maj_registre_uk_v1.py")


if __name__ == "__main__":
    main()
