#!/usr/bin/env python3
"""
sonde_bundles_v1.py — L'inspecteur web scripte, GENERALISE a n'importe quel
job board « application JavaScript » (SPA).

Meme technique que sonde_mig_v2, mais pour TOUS les pays : telecharge la
page, extrait ses bundles JS, et y cherche les URLs d'API et les parametres
sentant l'international (international*, visa, sponsor*, zielgruppe*,
shortage, penurie...). C'est ainsi qu'on classe chaque nouveau pays dans sa
famille de gisement sans ouvrir Safari.

    python scripts/sonde_bundles_v1.py                       # cibles par defaut
    python scripts/sonde_bundles_v1.py https://exemple.com   # cible libre

Cibles par defaut : Make it in Germany (en+de), work-in-luxembourg.lu
(plateforme ADEM « penurie » a vocation internationale), Actiris.
Lecture seule.
"""
from __future__ import annotations

import re
import sys
from urllib.parse import urljoin, urlparse

import requests

CIBLES_DEFAUT = [
    "https://www.make-it-in-germany.com/en/working-in-germany/job-listings",
    "https://www.make-it-in-germany.com/de/arbeiten-in-deutschland/stellenboerse",
    "https://www.work-in-luxembourg.lu/",
    "https://www.actiris.brussels/fr/citoyens/",
]
UA = {"User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                     "AppleWebKit/537.36 Chrome/126.0 Safari/537.36")}

MOTIF_API = re.compile(
    r"(?:https?:)?//(?:"
    r"(?:[\w\-]+\.)*(?:api|rest)[\w.\-]*/[\w/.\-]{0,140}"        # hote api.*/rest.*
    r"|[\w.\-]+/(?:v\d+/)?(?:api|rest|service|jobsuche|vacature"  # ou chemin /v1/api...
    r"|offres?|jobs?)[\w/.\-]{0,120})", re.I)
MOTIF_CLE = re.compile(
    r"[\"']?(X-API-Key|apikey|api[_-]?key)[\"']?\s*[:=]\s*[\"']([^\"']{4,60})[\"']",
    re.I)
MOTIF_PARAM = re.compile(
    r"[\"'&?{,\s(](internationale?\w*|visa\w*|sponsor\w*|zielgruppe\w*|"
    r"mig[A-Z]\w*|arbeitgeberdarstellung\w*|angebotsart|shortage\w*|"
    r"penurie\w*|foreign\w*|abroad)[\"']?\s*[:=]\s*[\"']?([\w\-]{1,40})",
    re.I)


def scripts_de(html: str, base_url: str) -> list[str]:
    urls = set()
    for m in re.finditer(r"<script[^>]+src=[\"']([^\"']+)[\"']", html, re.I):
        urls.add(urljoin(base_url, m.group(1)))
    for m in re.finditer(r"[\"']([^\"']+\.js(?:\?[^\"']*)?)[\"']", html):
        u = m.group(1)
        if u.startswith(("http", "/")):
            urls.add(urljoin(base_url, u))
    return sorted(urls)


def fouiller(nom: str, texte: str, t: dict) -> None:
    for m in MOTIF_API.finditer(texte):
        u = m.group(0)
        if u.endswith((".js", ".css", ".png", ".svg", ".woff", ".woff2")):
            continue
        t.setdefault("API", set()).add(f"[{nom}] {u[:150]}")
    for m in MOTIF_CLE.finditer(texte):
        t.setdefault("CLE", set()).add(f"[{nom}] {m.group(1)} = {m.group(2)}")
    for m in MOTIF_PARAM.finditer(texte):
        t.setdefault("PARAMETRES", set()).add(
            f"[{nom}] {m.group(1)} = {m.group(2)}")


def sonder(url: str) -> None:
    hote = urlparse(url).netloc
    print("\n" + "=" * 72 + f"\nCIBLE : {url}\n" + "=" * 72)
    t: dict[str, set] = {}
    try:
        r = requests.get(url, headers=UA, timeout=25)
        print(f"  page : HTTP {r.status_code}, {len(r.text)//1024} Ko")
        if not r.ok:
            return
        fouiller("html", r.text, t)
        js = scripts_de(r.text, url)
        print(f"  {len(js)} script(s)")
        for u in js[:25]:
            try:
                rj = requests.get(u, headers=UA, timeout=25, stream=True)
                corps = rj.raw.read(3_000_000, decode_content=True)
                nom = u.rsplit("/", 1)[-1][:36]
                print(f"    JS {rj.status_code} {len(corps)//1024:>5} Ko  {nom}")
                fouiller(nom, corps.decode("utf-8", errors="ignore"), t)
            except Exception as e:
                print(f"    JS ECHEC {u[:60]} : {e}")
    except Exception as e:
        print(f"  ECHEC : {e}")
        return
    if t:
        print(f"\n  --- trouvailles ({hote}) ---")
        for cat in ("API", "CLE", "PARAMETRES"):
            for v in sorted(t.get(cat, []))[:20]:
                print(f"  {cat:10} {v[:170]}")
    else:
        print("  rien d'exploitable dans les bundles (filtrage cote serveur).")


def main() -> None:
    cibles = [a for a in sys.argv[1:] if a.startswith("http")] or CIBLES_DEFAUT
    for c in cibles:
        sonder(c)
    print("\n===== FIN — glisse cette sortie dans la conversation =====")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        pass
