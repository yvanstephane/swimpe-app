#!/usr/bin/env python3
"""
sonde_europe.py — Les FAITS avant le code, pour FR / BE / GB / LU / ES.

  1. ADZUNA : quels pays tes cles couvrent-elles vraiment ?
     Test empirique sur fr, es, gb, be, lu, nl, it — 1 requete chacun.
  2. FRANCE TRAVAIL : l'API sans cle -> quel code HTTP ? (prouve le besoin
     du compte OAuth francetravail.io et donne l'URL du token.)
  3. REGISTRE DES SPONSORS UK (Home Office) : trouve le CSV du jour sur
     gov.uk, telecharge l'en-tete, compte les lignes, montre 3 exemples —
     la matiere premiere du « fglo=1 britannique ».

Lecture seule. Usage : python scripts/sonde_europe.py > europe.txt
"""
from __future__ import annotations

import csv
import io
import os
import re
from pathlib import Path

import requests

UA = {"User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                     "AppleWebKit/537.36 Chrome/126.0 Safari/537.36")}


def cles_adzuna():
    app_id = os.environ.get("ADZUNA_APP_ID", "")
    app_key = os.environ.get("ADZUNA_APP_KEY", "")
    if app_id and app_key:
        return app_id, app_key
    for env in (Path(".env"), Path("app/.env")):
        if env.exists():
            for l in env.read_text(encoding="utf-8", errors="ignore").splitlines():
                if l.startswith("ADZUNA_APP_ID"):
                    app_id = l.split("=", 1)[1].strip().strip("'\"")
                if l.startswith("ADZUNA_APP_KEY"):
                    app_key = l.split("=", 1)[1].strip().strip("'\"")
    return app_id, app_key


def titre(t):
    print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


def main() -> None:
    # ------------------------------------------------ 1. couverture Adzuna
    titre("1. ADZUNA — couverture reelle de TES cles")
    app_id, app_key = cles_adzuna()
    if not (app_id and app_key):
        print("  Cles ADZUNA_APP_ID / ADZUNA_APP_KEY introuvables (.env)")
    else:
        for cc in ("fr", "es", "gb", "be", "lu", "nl", "it"):
            try:
                r = requests.get(
                    f"https://api.adzuna.com/v1/api/jobs/{cc}/search/1",
                    params={"app_id": app_id, "app_key": app_key,
                            "results_per_page": 1, "what": "electrician"},
                    headers=UA, timeout=15)
                if r.ok:
                    n = r.json().get("count", "?")
                    print(f"  {cc}  OK   {n} offres au total")
                else:
                    print(f"  {cc}  {r.status_code}  {r.text[:80]}")
            except Exception as e:
                print(f"  {cc}  ECHEC {e}")

    # --------------------------------------------- 2. France Travail (auth)
    titre("2. FRANCE TRAVAIL — que dit l'API sans cle ?")
    try:
        r = requests.get(
            "https://api.francetravail.io/partenaire/offresdemploi"
            "/v2/offres/search",
            params={"motsCles": "electricien", "range": "0-1"},
            headers=UA, timeout=15)
        print(f"  HTTP {r.status_code}")
        print(f"  WWW-Authenticate : {r.headers.get('WWW-Authenticate','—')[:90]}")
        print(f"  corps : {r.text[:140]!r}")
        print("  -> compte gratuit sur francetravail.io requis ; token OAuth :")
        print("     https://entreprise.francetravail.fr/connexion/oauth2/"
              "access_token?realm=%2Fpartenaire")
    except Exception as e:
        print(f"  ECHEC : {e}")

    # ------------------------------------- 3. registre des sponsors (UK)
    titre("3. UK — registre officiel des sponsors (Home Office)")
    page = ("https://www.gov.uk/government/publications/"
            "register-of-licensed-sponsors-workers")
    try:
        r = requests.get(page, headers=UA, timeout=25)
        print(f"  page gov.uk : HTTP {r.status_code}")
        m = re.search(
            r"https://assets\.publishing\.service\.gov\.uk/[^\"']+\.csv",
            r.text)
        if not m:
            print("  aucun lien .csv trouve sur la page — colle-moi l'URL "
                  "visible sous 'Worker and Temporary Worker'.")
            return
        csv_url = m.group(0)
        print(f"  CSV du jour : {csv_url[:100]}…")
        rep = requests.get(csv_url, headers=UA, timeout=60, stream=True)
        brut = rep.raw.read(400_000, decode_content=True)
        texte = brut.decode("utf-8", errors="ignore")
        lignes = texte.splitlines()
        lecteur = csv.reader(io.StringIO(texte))
        entete = next(lecteur, [])
        print(f"  HTTP {rep.status_code} — colonnes : {entete}")
        exemples = [row for _, row in zip(range(3), lecteur)]
        for e in exemples:
            print(f"    ex : {e[:4]}")
        taille = rep.headers.get("Content-Length", "?")
        print(f"  taille totale annoncee : {taille} octets "
              f"(echantillon lu : {len(lignes)} lignes)")
        print("  -> matiere premiere du croisement Adzuna gb ∩ sponsors.")
    except Exception as e:
        print(f"  ECHEC : {e}")

    print("\n===== FIN — glisse europe.txt dans la conversation =====")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        pass
