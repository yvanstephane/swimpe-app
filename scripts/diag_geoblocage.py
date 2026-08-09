#!/usr/bin/env python3
"""
diag_geoblocage.py (v2) — Le CONTENU de l'offre est-il servi depuis l'etranger ?

La v1 etait fausse. Elle cherchait le texte "visiting Job Bank from outside
Canada" et concluait au blocage. Or ce texte est le POPUP d'avertissement,
present dans le HTML de toute page Job Bank : on le ferme, la page reste
lisible. D'ou des resultats contradictoires entre deux executions (le popup
tombait tantot dans, tantot hors de la troncature a 60 000 caracteres).

Adzuna, lui, REMPLACE le contenu :
    "Sorry, this job is not available in your region"
    "Search for similar jobs in your region"
Le poste n'est plus consultable.

Le bon critere n'est donc pas "un mur apparait" mais "les donnees de l'offre
sont-elles la ?". On cherche des marqueurs de contenu reel :
    - RDFa / schema.org : hiringOrganization, baseSalary, description
    - un titre de poste dans <h1>
et separement les marqueurs de substitution.

Verdict :
    SERVI       contenu present  -> le lien est utilisable depuis l'etranger
    SUBSTITUE   contenu remplace -> lien inutilisable pour un candidat hors pays
    AVERTI      contenu present + banniere -> utilisable, banniere informative

Lecture seule. Usage : python scripts/diag_geoblocage.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "app" / "api"))
sys.path.insert(0, str(RACINE))

import requests

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

# Le contenu de l'offre est-il present ?
CONTENU = re.compile(
    r'property=["\']?(hiringOrganization|baseSalary|description|datePosted)'
    r'|itemprop=["\']?(hiringOrganization|baseSalary)'
    r'|"@type"\s*:\s*"JobPosting"',
    re.I,
)

# Le contenu a-t-il ete REMPLACE par un ecran de substitution ?
SUBSTITUTION = re.compile(
    r"not available in your region"
    r"|n'est pas disponible dans votre r[ée]gion"
    r"|similar jobs in your region"
    r"|this (job|vacancy) has (been removed|expired)",
    re.I,
)

# Simple banniere informative, non bloquante.
AVERTISSEMENT = re.compile(
    r"visiting Job Bank from outside Canada"
    r"|vous [êe]tes actuellement [àa] l.ext[ée]rieur du Canada",
    re.I,
)


def tester(url: str) -> tuple[str, str]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
    except Exception as e:
        return "ERREUR", f"{type(e).__name__}"

    html = r.text                       # PAS de troncature : c'etait le bug v1
    a_contenu = bool(CONTENU.search(html))
    a_substitution = bool(SUBSTITUTION.search(html))
    a_avertissement = bool(AVERTISSEMENT.search(html))

    if a_substitution and not a_contenu:
        return "SUBSTITUE", f"{r.status_code}, contenu remplace"
    if a_contenu and a_avertissement:
        return "AVERTI", f"{r.status_code}, contenu present + banniere"
    if a_contenu:
        return "SERVI", f"{r.status_code}, {len(html)} octets"
    if a_substitution:
        return "SUBSTITUE", f"{r.status_code}"
    return "INDETERMINE", f"{r.status_code}, ni marqueur de contenu ni mur"


def main() -> None:
    from sources import registre

    cibles = [("adzuna", "CA", "metier"),
              ("adzuna", "FR", "stage"),
              ("jobbank_ca", "CA", "metier")]

    resume = {}
    for source, dest, type_p in cibles:
        src = registre.par_nom(source)
        if src is None or not src.couvre(dest, type_p):
            continue
        print(f"\n{'=' * 74}\n{source} — {dest} / {type_p}\n{'=' * 74}")
        try:
            offres = src.collecter(dest, type_p, mots_cles=None, limite=3)
        except Exception as e:
            print(f"  collecte impossible : {e}")
            continue
        if not offres:
            print("  aucune offre")
            continue

        verdicts = []
        for o in offres[:3]:
            verdict, detail = tester(o.url)
            verdicts.append(verdict)
            print(f"  {verdict:12} {detail:34} {o.titre[:30]}")
            print(f"    {o.url[:92]}")
        resume[f"{source}/{dest}"] = verdicts

    print(f"\n{'=' * 74}\nRESUME\n{'=' * 74}")
    for cle, v in resume.items():
        etat = "utilisable" if all(x in ("SERVI", "AVERTI") for x in v) else "INUTILISABLE"
        print(f"  {cle:18} {v}  -> {etat}")
    print("\n  SERVI / AVERTI : le candidat a l'etranger voit l'offre.")
    print("  SUBSTITUE      : le lien ne sert a rien pour lui.")


if __name__ == "__main__":
    main()
