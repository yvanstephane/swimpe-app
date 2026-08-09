#!/usr/bin/env python3
"""
sonde_mig.py — Deux verifications AVANT de promettre quoi que ce soit.

  1. L'API publique de la Bundesagentur (cle X-API-Key: jobboerse-jobsuche)
     repond-elle, avec pagination et details ?
  2. Quel PARAMETRE distingue les offres opt-in "Make it in Germany"
     (employeurs acceptant les candidatures etrangeres) ? On inspecte le
     HTML/JS de la page de resultats MIG a la recherche de l'appel API
     sous-jacent et de ses parametres.

Tant que le drapeau du point 2 n'est pas identifie, l'adaptateur mig_de
reste honnete : admissible_sans_permis = False.

Lecture seule. Usage : python scripts/sonde_mig.py
"""
from __future__ import annotations

import base64
import json
import re

import requests

API = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service"
HEAD = {"X-API-Key": "jobboerse-jobsuche",
        "User-Agent": "Mozilla/5.0 (Macintosh) Chrome/126.0",
        "Accept": "application/json"}

MIG_PAGES = [
    "https://www.make-it-in-germany.com/en/working-in-germany/job-listings",
    "https://www.make-it-in-germany.com/en/working-in-germany/job-listings/results?searchString=Elektriker",
]


def titre(t):
    print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


def main() -> None:
    # ------------------------------------------------------------ 1. liste
    titre("1. API BA — liste (was=Elektriker, size=5)")
    refnr = None
    try:
        r = requests.get(f"{API}/pc/v4/jobs", headers=HEAD, timeout=20,
                         params={"was": "Elektriker", "size": 5, "page": 1,
                                 "angebotsart": 1})
        r.raise_for_status()
        j = r.json()
        print(f"  HTTP {r.status_code} — maxErgebnisse={j.get('maxErgebnisse')}")
        for a in j.get("stellenangebote", [])[:5]:
            refnr = refnr or a.get("refnr")
            print(f"   - {a.get('titel','?')[:44]:46} "
                  f"{a.get('arbeitgeber','?')[:26]:28} "
                  f"{(a.get('arbeitsort') or {}).get('ort','?')}")
        print(f"  champs disponibles : {sorted(list((j.get('stellenangebote') or [{}])[0].keys()))[:12]} ...")
    except Exception as e:
        print(f"  ECHEC : {e}")
        print("  -> si 4xx : la cle publique a peut-etre change ; cherche")
        print("     'bund.dev jobsuche api key' pour la valeur actuelle.")

    # ---------------------------------------------------------- 2. detail
    titre("2. API BA — detail (description)")
    if refnr:
        try:
            b64 = base64.urlsafe_b64encode(refnr.encode()).decode().rstrip("=")
            r = requests.get(f"{API}/pc/v2/jobdetails/{b64}",
                             headers=HEAD, timeout=20)
            r.raise_for_status()
            j = r.json()
            desc = re.sub(r"\s+", " ", j.get("stellenbeschreibung", ""))[:180]
            print(f"  HTTP {r.status_code} — refnr={refnr}")
            print(f"  description : {desc!r}")
            print(f"  cles detail : {sorted(j.keys())[:14]} ...")
        except Exception as e:
            print(f"  ECHEC : {e}")
    else:
        print("  saute (pas de refnr en 1)")

    # ------------------------------------------ 3. drapeau opt-in MIG ?
    titre("3. Page MIG — a la recherche du parametre opt-in international")
    indices = set()
    for url in MIG_PAGES:
        try:
            r = requests.get(url, timeout=25,
                             headers={"User-Agent": HEAD["User-Agent"]})
            print(f"  {r.status_code}  {url[:70]}")
            html = r.text
            for m in re.finditer(
                    r"(rest\.arbeitsagentur\.de[^\"'\\s]{0,160})", html):
                indices.add("API: " + m.group(1)[:160])
            for m in re.finditer(
                    r"[?&](internationale?\w*|migType|mig|veroeffentl\w*|"
                    r"zielgruppe\w*|arbeitgeberdarstellung\w*)=([\w\-]+)",
                    html, re.I):
                indices.add(f"PARAM: {m.group(1)}={m.group(2)}")
            for m in re.finditer(
                    r'"(internationale?\w*|zielgruppe\w*)"\s*:\s*"?([\w\-]+)',
                    html, re.I):
                indices.add(f"JSON: {m.group(1)}={m.group(2)}")
        except Exception as e:
            print(f"  ECHEC {url[:60]} : {e}")

    if indices:
        print("\n  INDICES TROUVES (a m'envoyer) :")
        for i in sorted(indices):
            print("   ", i[:150])
    else:
        print("\n  Aucun indice dans le HTML statique — le filtre est sans")
        print("  doute applique cote serveur MIG. Plan B : ouvrir la page")
        print("  resultats MIG dans Safari > Develop > Show Web Inspector >")
        print("  Network, chercher 'arbeitsagentur' et copier l'URL complete")
        print("  de la requete — elle contient le parametre qui nous manque.")

    print("\n===== FIN — colle toute la sortie =====")


if __name__ == "__main__":
    main()
