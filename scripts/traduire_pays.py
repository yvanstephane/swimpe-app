#!/usr/bin/env python3
"""
traduire_pays.py — Noms de pays dans TOUTES les langues, sans Ollama.

Les noms de pays ont des traductions officielles : le CLDR d'Unicode, livre
avec Babel. Aucune hallucination possible, aucune requete reseau, instantane.

  python scripts/traduire_pays.py                  # toutes les langues de LANGUES
  python scripts/traduire_pays.py de ko            # seulement celles-ci
  python scripts/traduire_pays.py --verifier       # rapport, n'ecrit rien

Ecrit data/i18n/pays.json : {"Allemagne": {"de": "Deutschland", ...}, ...}
que pays_i18n.nom_pays() charge en surcouche (voir patch_pays.py).
Les traductions DEJA presentes dans PAYS ne sont jamais ecrasees.

Prerequis : pip install babel
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "app" / "api"))

try:
    from babel import Locale
except ImportError:
    print("Babel manquant :  pip install babel")
    sys.exit(1)

# Noms francais de Yorbity absents du CLDR ou ecrits autrement.
ALIAS = {
    "republique tcheque": "CZ", "coree du sud": "KR", "coree du nord": "KP",
    "etats-unis": "US", "emirats arabes unis": "AE", "cap-vert": "CV",
    "cote d'ivoire": "CI", "congo (rdc)": "CD", "congo (brazzaville)": "CG",
    "republique dominicaine": "DO", "royaume-uni": "GB", "birmanie": "MM",
    "timor oriental": "TL", "vatican": "VA", "palestine": "PS",
    "swaziland": "SZ", "macedoine du nord": "MK", "bielorussie": "BY",
    "moldavie": "MD", "centrafrique": "CF", "vietnam": "VN",
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").strip().lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("\u2019", "'").replace("\u02bc", "'")
    return re.sub(r"\s+", " ", s)


def index_fr() -> dict[str, str]:
    """nom francais normalise -> code ISO2 (CLDR + alias)."""
    idx = {}
    for code, nom in Locale("fr").territories.items():
        if len(code) == 2:
            idx.setdefault(_norm(nom), code)
    idx.update(ALIAS)
    return idx


def main() -> None:
    verif = "--verifier" in sys.argv
    demandees = [a for a in sys.argv[1:] if not a.startswith("-")]

    import i18n
    import pays_i18n
    langues = demandees or [c for c in i18n.LANGUES if c != "fr"]
    idx = index_fr()

    surcouche: dict[str, dict] = {}
    fichier = RACINE / "data" / "i18n" / "pays.json"
    if fichier.exists():
        surcouche = json.loads(fichier.read_text(encoding="utf-8"))

    introuvables, ajouts = [], 0
    for nom_fr in pays_i18n.PAYS:
        code = idx.get(_norm(nom_fr))
        if not code:
            introuvables.append(nom_fr)
            continue
        deja = pays_i18n.PAYS.get(nom_fr, {})
        for lg in langues:
            if deja.get(lg):                      # traduction humaine : intouchable
                continue
            try:
                nom = Locale(lg).territories.get(code)
            except Exception:
                nom = None
            if nom:
                surcouche.setdefault(nom_fr, {})[lg] = nom
                ajouts += 1

    print(f"{len(pays_i18n.PAYS)} pays · langues {langues}")
    print(f"{ajouts} traduction(s) generee(s), {len(introuvables)} pays non apparie(s)")
    if introuvables:
        print("  non apparies (ajoute-les a ALIAS) :")
        for n in introuvables:
            print("   -", n)

    if verif:
        print("\n--verifier : rien ecrit.")
        return
    fichier.parent.mkdir(parents=True, exist_ok=True)
    fichier.write_text(json.dumps(surcouche, ensure_ascii=False, indent=1,
                                  sort_keys=True), encoding="utf-8")
    print(f"\n-> {fichier.relative_to(RACINE)}")


if __name__ == "__main__":
    main()
