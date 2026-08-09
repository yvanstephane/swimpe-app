#!/usr/bin/env python3
"""
diag_jobbank.py — Trouve les bons selecteurs CSS sur une vraie page d'offre.
Usage :  python scripts/diag_jobbank.py
Aucune modification. Lecture seule. Affiche ce qui matche.
"""
import re
import sys

sys.path.insert(0, ".")

from bs4 import BeautifulSoup
import app.api.jobbank_intl as j

CANDIDATS = {
    "employeur": [
        '[property="hiringOrganization"]',
        '[property="hiringOrganization"] [property="name"]',
        ".company",
        "#hiringOrganization",
        'span[property="name"]',
        ".job-posting-brief strong",
        ".title strong",
    ],
    "lieu": [
        '[property="addressLocality"]',
        '[property="jobLocation"]',
        ".address",
        "#location",
        ".location",
    ],
    "description": [
        "div.job-posting-detail-requirements",
        "#job-posting-detail-body",
        '[property="description"]',
        "#JobPostingDetailBody",
        ".job-posting-detail-content",
    ],
    "date": [
        '[property="datePosted"]',
        ".date-posted",
        "#datePosted",
        "time",
    ],
    "salaire": [
        '[property="baseSalary"]',
        ".salary",
    ],
}


def main() -> None:
    cartes = j._collecter_feed("student", "en", 5, 25)
    if not cartes:
        print("[!] Le flux ne renvoie rien. Verifie la connexion.")
        return

    url = cartes[0]["url"]
    print(f"URL testee : {url}\n")

    html = j._session().get(url, timeout=25).text
    soup = BeautifulSoup(html, "html.parser")

    for champ, selecteurs in CANDIDATS.items():
        print(f"--- {champ}")
        trouve = False
        for sel in selecteurs:
            el = soup.select_one(sel)
            if el:
                trouve = True
                val = el.get_text(" ", strip=True)[:80]
                print(f"  HIT   {sel:48} -> {val!r}")
            else:
                print(f"  miss  {sel}")
        if not trouve:
            print("  >>> AUCUN selecteur ne matche.")
        print()

    # Reference : plusieurs formulations possibles
    print("--- reference")
    motifs = [
        r"Job\s*Bank\s*Job\s*number\s*[:\-]?\s*([0-9]{5,})",
        r"Job\s*number\s*[:\-]?\s*([0-9]{5,})",
        r"Numero\s*de\s*poste\s*[:\-]?\s*([0-9]{5,})",
        r"/jobposting/(\d+)",
    ]
    for m in motifs:
        r = re.search(m, html, re.I)
        print(f"  {'HIT ' if r else 'miss'} {m:55} -> {r.group(1) if r else None}")

    # Donnees structurees JSON-LD : souvent le plus fiable
    print("\n--- JSON-LD (schema.org JobPosting)")
    blocs = soup.find_all("script", type="application/ld+json")
    if not blocs:
        print("  aucun bloc ld+json")
    for b in blocs[:2]:
        txt = (b.string or "")[:600]
        print(f"  {txt}\n")


if __name__ == "__main__":
    main()
