#!/usr/bin/env python3
"""
patch_uk_lien_v1.py — Le lien des offres UK devient utilisable partout.

PREUVE (capture du 2026-07-10) : le lien direct Adzuna (click.appcast.io)
repond « This job is not available in your area » hors du Royaume-Uni —
cul-de-sac pour 100 % du public Yorbity, admin compris.

CORRECTIF (meme parade que l'Allemagne) : chaque offre pointe vers la
recherche titre+employeur sur Find a Job (findajob.dwp.gov.uk), le job
board du gouvernement britannique — accessible du monde entier. Et
lien_accessible_depuis_etranger passe a True : le toggle admin peut
desormais montrer ces liens aux visiteurs sans les envoyer dans un mur.

Honnetete : la recherche retombe sur l'annonce ou ses jumelles chez le
meme employeur ; si l'annonce n'est pas relayee sur Find a Job, le
candidat voit les autres postes du meme sponsor — jamais un ecran de blocage.

Idempotent. Sauvegarde .bak. Syntaxe verifiee, restauration si casse.
Usage : python scripts/patch_uk_lien_v1.py [--dry]
"""
from __future__ import annotations

import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DRY = "--dry" in sys.argv
P = RACINE / "app" / "api" / "sources" / "uk_sponsors.py"

A_IMPORT = "import requests"
R_IMPORT = "import urllib.parse as _up\n\nimport requests"

A_ACCES = '''    def lien_accessible_depuis_etranger(self, destination, type_projet) -> bool:
        return False           # liens Adzuna substitues hors domaine national'''
R_ACCES = '''    def lien_accessible_depuis_etranger(self, destination, type_projet) -> bool:
        return True   # liens Find a Job (gov.uk) : accessibles du monde entier
                      # (le lien Adzuna direct etait geo-bloque — patch_uk_lien)'''

A_URL = '''        url = a.get("redirect_url", "")'''
R_URL = '''        # Le lien Adzuna direct (click.appcast.io) est geo-bloque hors UK
        # (« This job is not available in your area », constate 2026-07-10).
        # -> recherche titre+employeur sur le portail officiel Find a Job,
        # accessible partout (meme parade que l'Allemagne).
        _entreprise = (a.get("company") or {}).get("display_name", "")
        url = ("https://findajob.dwp.gov.uk/search?q="
               + _up.quote_plus(f"{a.get('title', '')} {_entreprise}".strip()))'''


def main() -> None:
    src = P.read_text(encoding="utf-8")
    if "findajob.dwp.gov.uk" in src:
        print("= uk_sponsors.py : lien Find a Job deja en place")
        return
    n = 0
    for a, r in ((A_IMPORT, R_IMPORT), (A_ACCES, R_ACCES), (A_URL, R_URL)):
        if a in src:
            src = src.replace(a, r, 1); n += 1
        else:
            print(f"? ancre absente : {a[:50]!r}…")
    if n != 3:
        print(f"? {n}/3 retouches seulement — RIEN ecrit")
        sys.exit(2)
    if DRY:
        print("~ uk_sponsors.py : 3 retouches [DRY-RUN]")
        return
    ast.parse(src)
    bak = P.with_suffix(f".py.bak-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(P, bak)
    P.write_text(src, encoding="utf-8")
    print(f"v uk_sponsors.py : 3 retouches ({bak.name})")
    print("Vide le cache offres puis relance pour regenerer les liens.")


if __name__ == "__main__":
    main()
