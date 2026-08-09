#!/usr/bin/env python3
"""
patch_fixpack_v1.py — Deux correctifs de fond.

A. traduction.py (la racine du faux anglais / faux allemand) :
   1. nom_langue() : dictionnaire complete (de, it) + SECOURS CLDR via
      Babel pour toute langue future — le prompt ne recevra plus jamais
      un code brut ("vers le de"). Langue inconnue de Babel -> on ne
      traduit PAS (repli francais), on n'empoisonne pas le cache.
   2. Prompt verrouille : « Reponds UNIQUEMENT dans cette langue,
      jamais en francais. »
   3. Garde-fou avant cache : une « traduction » restee en francais
      (marqueurs exclusivement francais : vous, tes, aux, avec, pour,
      c'est, d'un, etre) ou identique au texte source n'est JAMAIS mise
      en cache — elle sera retentee au prochain affichage.

B. sources/uk_sponsors.py : dedoublonnage des offres Adzuna
   (titre+employeur) — fini les trois « BAE Systems | Electrician ».

Idempotent. Sauvegardes .bak. Syntaxe verifiee, restauration si casse.
Usage : python scripts/patch_fixpack_v1.py [--dry]
"""
from __future__ import annotations

import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DRY = "--dry" in sys.argv
HORO = datetime.now().strftime("%Y%m%d-%H%M%S")
resultats: list[str] = []


def ecrire(p: Path, contenu: str, n: int) -> None:
    if DRY:
        resultats.append(f"~ {p.name} : {n} retouche(s) [DRY-RUN]")
        return
    bak = p.with_suffix(p.suffix + f".bak-{HORO}")
    shutil.copy2(p, bak)
    p.write_text(contenu, encoding="utf-8")
    try:
        ast.parse(contenu)
    except SyntaxError as e:
        shutil.copy2(bak, p)
        resultats.append(f"x {p.name} : syntaxe cassee l.{e.lineno} — restaure")
        return
    resultats.append(f"v {p.name} : {n} retouche(s) ({bak.name})")


# =========================================================================== #
# A. traduction.py
# =========================================================================== #
A1 = '''LANGUE_NOM = {
    "en":"anglais","es":"espagnol","pt":"portugais","zh":"chinois (simplifié)",
    "ar":"arabe","ja":"japonais","ko":"coréen","id":"indonésien",
}'''
R1 = '''LANGUE_NOM = {
    "en":"anglais","es":"espagnol","pt":"portugais","zh":"chinois (simplifié)",
    "ar":"arabe","ja":"japonais","ko":"coréen","id":"indonésien",
    "de":"allemand","it":"italien",
}


def nom_langue(lang):
    """Nom francais de la langue cible (patch_fixpack). Secours CLDR via
    Babel pour toute langue future ; None = langue inconnue -> on ne
    traduit pas plutot que d'envoyer un code brut au modele."""
    if lang in LANGUE_NOM:
        return LANGUE_NOM[lang]
    try:
        from babel import Locale
        n = Locale(lang).get_display_name("fr")
        if n and n.lower() != lang.lower():
            return n
    except Exception:
        pass
    return None


# Marqueurs EXCLUSIVEMENT francais (absents de l'italien, l'allemand,
# l'espagnol...) : s'ils abondent, la « traduction » est restee en francais.
_STOP_FR = (" vous ", " tes ", " c'est ", " d'un ", " aux ",
            " avec ", " pour ", " être ")


def _semble_francais(texte, lang):
    if lang == "fr" or not texte:
        return False
    t = " " + texte.lower().replace("\\u2019", "'") + " "
    return sum(t.count(s) for s in _STOP_FR) >= 2'''

A2 = '''    langue = LANGUE_NOM.get(lang, lang)
    prompt = (f"Traduis le texte suivant du français vers le {langue}. "'''
R2 = '''    langue = nom_langue(lang)
    if not langue:                      # patch_fixpack : jamais de code brut
        return None
    prompt = (f"Traduis le texte suivant du français vers le {langue}. "
              f"Réponds UNIQUEMENT dans cette langue ({langue}), jamais en français. "'''

A3 = '''    trad = _appel_ollama(texte, lang)
    if trad:
        _au_cache(texte, lang, trad)
        return trad'''
R3 = '''    trad = _appel_ollama(texte, lang)
    if trad and trad.strip() != texte.strip() and not _semble_francais(trad, lang):
        _au_cache(texte, lang, trad)    # patch_fixpack : jamais de francais
        return trad                     # ni d'echo en cache'''


def patch_traduction() -> None:
    p = RACINE / "app" / "api" / "traduction.py"
    src = p.read_text(encoding="utf-8")
    if "nom_langue" in src:
        resultats.append("= traduction.py : deja patche")
        return
    n = 0
    for a, r in ((A1, R1), (A2, R2), (A3, R3)):
        if a in src:
            src = src.replace(a, r, 1); n += 1
        else:
            resultats.append(f"? traduction.py : ancre absente ({a[:38]!r}…)")
    if n == 3:
        ecrire(p, src, n)
    elif n:
        resultats.append(f"? traduction.py : {n}/3 seulement — RIEN ecrit")


# =========================================================================== #
# B. uk_sponsors.py — dedoublonnage
# =========================================================================== #
A_UK = '''        filtrees = [a for a in brutes
                    if REGISTRE_HO.est_sponsor(
                        (a.get("company") or {}).get("display_name", ""))]'''
R_UK = A_UK + '''
        # Dedoublonnage titre+employeur (patch_fixpack) : Adzuna renvoie
        # souvent la meme annonce plusieurs fois.
        _vues, _dedup = set(), []
        for a in filtrees:
            k = ((a.get("title") or "").strip().lower(),
                 ((a.get("company") or {}).get("display_name") or "").lower())
            if k not in _vues:
                _vues.add(k)
                _dedup.append(a)
        filtrees = _dedup'''


def patch_uk() -> None:
    p = RACINE / "app" / "api" / "sources" / "uk_sponsors.py"
    if not p.exists():
        resultats.append("- uk_sponsors.py absent")
        return
    src = p.read_text(encoding="utf-8")
    if "_dedup" in src:
        resultats.append("= uk_sponsors.py : dedoublonnage deja en place")
        return
    if A_UK not in src:
        resultats.append("? uk_sponsors.py : ancre filtre introuvable")
        return
    ecrire(p, src.replace(A_UK, R_UK, 1), 1)


def main() -> None:
    if DRY:
        print(">>> DRY-RUN\n")
    patch_traduction()
    patch_uk()
    print()
    for r in resultats:
        print(" ", r)
    if any(r.startswith("x") for r in resultats):
        sys.exit(1)
    if any(r.startswith("?") for r in resultats):
        sys.exit(2)
    print("\nFINI — purge ensuite le cache pollue : "
          "python scripts/purger_trad_v1.py de it --polluees")


if __name__ == "__main__":
    main()
