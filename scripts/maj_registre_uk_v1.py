#!/usr/bin/env python3
"""
maj_registre_uk_v1.py — Telecharge le registre officiel des sponsors
(Home Office) vers data/uk_sponsors.csv. A relancer chaque mois (le
Home Office publie une nouvelle version reguliere).

  python scripts/maj_registre_uk_v1.py

Trouve le lien .csv du jour sur la page gov.uk, telecharge en streaming
(le fichier fait plusieurs dizaines de Mo), verifie l'en-tete, affiche
le nombre d'employeurs. Lecture seule cote gov.uk ; ecrit uniquement
data/uk_sponsors.csv (+ .date temoin).
"""
from __future__ import annotations

import csv
import io
import re
import sys
from datetime import date
from pathlib import Path

import requests

RACINE = Path(__file__).resolve().parent.parent
CIBLE = RACINE / "data" / "uk_sponsors.csv"
PAGE = ("https://www.gov.uk/government/publications/"
        "register-of-licensed-sponsors-workers")
UA = {"User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                     "AppleWebKit/537.36 Chrome/126.0 Safari/537.36")}


def main() -> None:
    print(f"page : {PAGE}")
    r = requests.get(PAGE, headers=UA, timeout=30)
    r.raise_for_status()
    m = re.search(
        r"https://assets\.publishing\.service\.gov\.uk/[^\"']+\.csv", r.text)
    if not m:
        print("Aucun lien .csv sur la page — le format gov.uk a change ; "
              "colle-moi la section 'Documents' de la page.")
        sys.exit(2)
    url = m.group(0)
    print(f"CSV  : {url}")

    CIBLE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CIBLE.with_suffix(".csv.tmp")
    total = 0
    with requests.get(url, headers=UA, timeout=120, stream=True) as rep:
        rep.raise_for_status()
        with tmp.open("wb") as f:
            for morceau in rep.iter_content(1 << 20):
                f.write(morceau)
                total += len(morceau)
                print(f"\r  {total/1e6:6.1f} Mo", end="", flush=True)
    print()

    # verification de l'en-tete avant de remplacer
    with tmp.open(encoding="utf-8", errors="ignore", newline="") as f:
        entete = next(csv.reader(f), [])
    if not any("organisation" in c.lower() for c in entete):
        print(f"En-tete inattendu : {entete} — fichier garde en .tmp, "
              "rien remplace.")
        sys.exit(2)
    n = sum(1 for _ in tmp.open(encoding="utf-8", errors="ignore")) - 1
    tmp.replace(CIBLE)
    CIBLE.with_suffix(".date").write_text(date.today().isoformat())
    print(f"OK : {CIBLE.name} — {n:,} lignes, colonnes {entete[:4]}…"
          .replace(",", " "))
    print("Relance l'app : la source uk_sponsors se chargera toute seule.")


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as e:
        print(f"ECHEC reseau : {e}")
        sys.exit(1)
