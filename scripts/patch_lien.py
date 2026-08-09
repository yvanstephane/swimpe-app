#!/usr/bin/env python3
"""
patch_lien.py — Masque au visiteur les liens geo-bloques (Adzuna), garde
ceux qui s'ouvrent partout (Job Bank). L'admin voit toujours tout.

Contexte (diag_geoblocage.py, 2026-07-10) :
  adzuna.ca depuis la France -> SUBSTITUE ("not available in your region")
  jobbank.gc.ca              -> AVERTI (banniere, contenu servi)
Le blocage est cote Adzuna, par IP du visiteur : rien a "debloquer" chez nous.
Mais l'API Adzuna, elle, passe partout — la carte s'affiche. Seul le lien
sortant mene a un mur pour un visiteur en Afrique, Asie ou Amerique du Sud.

registre.collecter() pose desormais `lien_accessible` sur chaque offre.
Ce patch change UNE ligne de jobs_api.py :

  avant : if o["url"] and (admin or _liens):
  apres : if o.get("url") and (admin or (_liens and o.get("lien_accessible", True))):

Consequence : le toggle admin "Montrer les liens" ne peut plus exposer un
lien Adzuna a un visiteur — il ne gouverne que les liens accessibles.

Idempotent. Sauvegarde .bak. Verifie la syntaxe, restaure si casse.
Usage : python scripts/patch_lien.py [--dry]
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
P = RACINE / "app" / "api" / "jobs_api.py"

AVANT = re.compile(r'if o\["url"\] and \(admin or _liens\):')
APRES = 'if o.get("url") and (admin or (_liens and o.get("lien_accessible", True))):'


def main() -> None:
    if not P.exists():
        print("jobs_api.py introuvable")
        sys.exit(1)
    src = P.read_text(encoding="utf-8")

    if APRES in src:
        print("= jobs_api.py : deja patche")
        return
    if not AVANT.search(src):
        print("? jobs_api.py : ligne attendue introuvable — rien ecrit.")
        print("  Cherche manuellement : grep -n 'admin or _liens' app/api/jobs_api.py")
        sys.exit(2)

    if DRY:
        print("~ jobs_api.py : 1 patch [DRY-RUN]")
        return

    bak = P.with_suffix(f".py.bak-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(P, bak)
    src = AVANT.sub(APRES, src, count=1)
    P.write_text(src, encoding="utf-8")
    try:
        ast.parse(src)
    except SyntaxError as e:
        shutil.copy2(bak, P)
        print(f"x SYNTAXE CASSEE ligne {e.lineno} — restaure depuis {bak.name}")
        sys.exit(1)
    print(f"v jobs_api.py : 1 patch, syntaxe OK ({bak.name})")
    print("\nVide le cache (les offres deja en cache n'ont pas le champ) :")
    print("  python -c \"import sqlite3;c=sqlite3.connect('data/mobilite.db',timeout=30);"
          "c.execute('DELETE FROM jobs_cache');c.commit();print('cache vide')\"")


if __name__ == "__main__":
    main()
