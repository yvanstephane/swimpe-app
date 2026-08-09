#!/usr/bin/env python3
"""
patch_pays.py — Deux retouches dans pays_i18n.py.

  1. SURCOUCHE : nom_pays() charge data/i18n/pays.json (genere par
     traduire_pays.py depuis le CLDR d'Unicode). Les traductions ecrites
     a la main dans PAYS gardent la priorite. Une langue absente retombe
     sur le francais — jamais de plantage.

  2. HONNETETE : T_PLUS["accompagne"] portait encore l'ancienne promesse
     pour ja/ko/id (« on t'accompagne JUSQU'AU BOUT / jusqu'a »), alors que
     les six autres langues disent desormais « dans ton projet ». On aligne :
       ja  最後までサポートします      -> あなたのプロジェクトに寄り添います —
       ko  끝까지 함께합니다           -> 당신의 프로젝트를 함께합니다 —
       id  Kami dampingi kamu hingga -> Kami dampingi proyekmu —

Idempotent. Sauvegarde .bak. Syntaxe verifiee, restauration si casse.
Usage : python scripts/patch_pays.py [--dry]
"""
from __future__ import annotations

import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DRY = "--dry" in sys.argv
P = RACINE / "app" / "api" / "pays_i18n.py"

A_NOM_PAYS = '''def nom_pays(nom_fr, lang):
    """Traduit un nom de pays. Repli sur le nom FR si absent."""
    if lang == "fr":
        return nom_fr
    return PAYS.get(nom_fr, {}).get(lang, nom_fr)'''

R_NOM_PAYS = '''# --- Surcouche CLDR (patch_pays) ---------------------------------------------
# data/i18n/pays.json, genere par scripts/traduire_pays.py depuis le CLDR
# d'Unicode : noms officiels, aucune hallucination. Les traductions ecrites
# a la main dans PAYS gardent la priorite.
_SURCOUCHE_PAYS = {}


def _charger_surcouche_pays():
    import json
    from pathlib import Path as _P
    for base in (_P("data") / "i18n" / "pays.json",
                 _P(__file__).resolve().parents[2] / "data" / "i18n" / "pays.json"):
        try:
            if base.exists():
                _SURCOUCHE_PAYS.update(json.loads(base.read_text(encoding="utf-8")))
                return
        except Exception:
            pass


_charger_surcouche_pays()


def nom_pays(nom_fr, lang):
    """Traduit un nom de pays. Priorite : PAYS (humain) > surcouche CLDR > FR."""
    if lang == "fr":
        return nom_fr
    humain = PAYS.get(nom_fr, {}).get(lang)
    if humain:
        return humain
    return _SURCOUCHE_PAYS.get(nom_fr, {}).get(lang, nom_fr)'''

REFORMULATIONS = [
    ('"accompagne": {"ja":"🤝 最後までサポートします：","ko":"🤝 끝까지 함께합니다：","id":"🤝 Kami dampingi kamu hingga"},',
     '"accompagne": {"ja":"🤝 あなたのプロジェクトに寄り添います —","ko":"🤝 당신의 프로젝트를 함께합니다 —","id":"🤝 Kami dampingi proyekmu —"},'),
]


def main() -> None:
    if not P.exists():
        print("pays_i18n.py introuvable")
        sys.exit(1)
    src = P.read_text(encoding="utf-8")
    if "_SURCOUCHE_PAYS" in src:
        print("= pays_i18n.py : deja patche")
        return
    if A_NOM_PAYS not in src:
        print("? pays_i18n.py : nom_pays() introuvable a l'identique — rien ecrit")
        sys.exit(2)

    n = 0
    src = src.replace(A_NOM_PAYS, R_NOM_PAYS, 1); n += 1
    for avant, apres in REFORMULATIONS:
        if avant in src:
            src = src.replace(avant, apres, 1); n += 1
        else:
            print("? reformulation 'accompagne' ja/ko/id : ligne non trouvee (sautee)")

    if DRY:
        print(f"~ pays_i18n.py : {n} retouche(s) [DRY-RUN]")
        return
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"x syntaxe cassee l.{e.lineno} — rien ecrit")
        sys.exit(1)
    bak = P.with_suffix(f".py.bak-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(P, bak)
    P.write_text(src, encoding="utf-8")
    print(f"v pays_i18n.py : {n} retouche(s), syntaxe OK ({bak.name})")


if __name__ == "__main__":
    main()
