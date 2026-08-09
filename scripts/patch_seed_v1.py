#!/usr/bin/env python3
"""
patch_seed_v1.py — Fin structurelle du « database is locked » au demarrage.

CAUSE (ui.py:795-803) : db() inserait les 196 pays dans config_pays a
CHAQUE rerun de CHAQUE onglet (INSERT OR IGNORE x196 + commit). Deux
onglets ouverts = deux ecrivains en collision permanente ; la patience
SQLite (30 s) absorbe les frottements, pas un conflit repete.

CORRECTIF : un SELECT COUNT (lecture, jamais bloquante) decide ; on
n'ecrit que si des pays MANQUENT — une fois par vie de la base, ou quand
ORIGINES_MONDE grandit. Zero ecriture au rerun ordinaire.

Idempotent. Sauvegarde .bak. Syntaxe verifiee, restauration si casse.
Usage : python scripts/patch_seed_v1.py [--dry]
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

ANCIEN = '''    for code in D:
        con.execute("INSERT OR IGNORE INTO config_pays(code,actif) VALUES(?,1)", (code,))
    con.commit()'''

NOUVEAU = '''    # Seed des pays UNIQUEMENT s'il en manque (patch_seed_v1) : plus
    # d'ecriture a chaque rerun -> plus de collision entre onglets.
    _n = con.execute("SELECT COUNT(*) FROM config_pays").fetchone()[0]
    if _n < len(D):
        for code in D:
            con.execute("INSERT OR IGNORE INTO config_pays(code,actif) VALUES(?,1)", (code,))
        con.commit()'''


def main() -> None:
    src = P.read_text(encoding="utf-8")
    if "patch_seed_v1" in src:
        print("= ui.py : seed deja garde")
        return
    if ANCIEN not in src:
        print("? ui.py : bloc seed introuvable a l'identique — envoie "
              "sed -n '795,806p' app/api/ui.py")
        sys.exit(2)
    if DRY:
        print("~ ui.py : 1 retouche [DRY-RUN]")
        return
    nouveau = src.replace(ANCIEN, NOUVEAU, 1)
    ast.parse(nouveau)
    bak = P.with_suffix(f".py.bak-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(P, bak)
    P.write_text(nouveau, encoding="utf-8")
    print(f"v ui.py : seed garde par comptage ({bak.name})")


if __name__ == "__main__":
    main()
