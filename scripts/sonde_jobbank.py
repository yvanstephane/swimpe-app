#!/usr/bin/env python3
"""
sonde_jobbank.py — Trouve le VRAI filtre "emploi etudiant" de Job Bank.

Teste une matrice de parametres sur le flux Atom et compare :
  - le nombre total de resultats
  - combien de titres contiennent reellement un mot etudiant
  - un echantillon de titres

Parametres connus (releves dans les URL indexees par Job Bank) :
  jkw=<mot>    mot-cle "job keyword"  (candidat serieux)
  dkw=<mot>    filtre partiellement, matche le boilerplate d'inclusion
  fsrc=21      Summer Jobs
  fsrc=32      Temporary Foreign Workers
  fsrc=16      Canada Summer Jobs
  fglo=1       Canadians AND international candidates
  fper=L|P     permanence
  fexp=0       aucune experience requise

Lecture seule. Aucune modification. ~20 requetes, 1 s d'intervalle.
Usage : python scripts/sonde_jobbank.py
"""
from __future__ import annotations

import re
import sys
import time
from urllib.parse import urlencode
from xml.etree import ElementTree as ET

sys.path.insert(0, ".")
import app.api.jobbank_intl as j  # noqa: E402

FEED = "https://www.jobbank.gc.ca/jobsearch/feed/jobSearchRSSfeed"
ATOM = "{http://www.w3.org/2005/Atom}"

TITRE_ETUDIANT = re.compile(
    r"\b(student|intern|internship|apprentice|co-?op|trainee|summer)s?\b", re.I
)

# (libelle, dict de parametres)
ESSAIS = [
    ("reference : rien",                {}),
    ("fglo=1 seul",                     {"fglo": 1}),
    ("dkw=student",                     {"dkw": "student"}),
    ("jkw=student",                     {"jkw": "student"}),
    ("jkw=student + fglo",              {"jkw": "student", "fglo": 1}),
    ("searchstring=student",            {"searchstring": "student"}),
    ("fsrc=21 (Summer Jobs)",           {"fsrc": 21}),
    ("fsrc=21 + fglo",                  {"fsrc": 21, "fglo": 1}),
    ("fsrc=16 (Canada Summer Jobs)",    {"fsrc": 16}),
    ("fsrc=32 (Temp Foreign Workers)",  {"fsrc": 32}),
    ("fexp=0 (sans experience)",        {"fexp": 0}),
    ("fexp=0 + fglo",                   {"fexp": 0, "fglo": 1}),
    ("jkw=intern",                      {"jkw": "intern"}),
    ("jkw=apprentice",                  {"jkw": "apprentice"}),
    ("jkw=apprentice + fglo",           {"jkw": "apprentice", "fglo": 1}),
    ("jkw=co-op",                       {"jkw": "co-op"}),
]


def titres(params: dict, rows: int = 50, timeout: int = 25) -> list[str] | None:
    p = dict(params)
    p.update({"sort": "D", "rows": rows, "lang": "en"})
    try:
        r = j._session().get(f"{FEED}?{urlencode(p)}", timeout=timeout)
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except Exception as e:
        print(f"    ERREUR {e}")
        return None
    out = []
    for e in root.findall(ATOM + "entry"):
        t = e.find(ATOM + "title")
        out.append((t.text or "").strip() if t is not None else "")
    return out


def main() -> None:
    print(f"{'essai':32} {'total':>6} {'titres etudiants':>17}   exemples")
    print("-" * 100)
    ref = None
    for libelle, params in ESSAIS:
        t = titres(params)
        time.sleep(1.0)
        if t is None:
            continue
        if ref is None:
            ref = len(t)
        hits = [x for x in t if TITRE_ETUDIANT.search(x)]
        marque = ""
        if len(t) != ref and len(t) > 0:
            marque = " <- FILTRE"
        if hits:
            marque += "  *** TITRES ETUDIANTS ***"
        ex = ", ".join(x[:26] for x in (hits or t)[:2])
        print(f"{libelle:32} {len(t):>6} {len(hits):>17}   {ex}{marque}")

    print("\nLecture :")
    print("  total identique a la reference  -> le parametre est ignore")
    print("  total different                 -> le parametre filtre")
    print("  titres etudiants > 0            -> c'est CE filtre qu'il faut")


if __name__ == "__main__":
    main()
