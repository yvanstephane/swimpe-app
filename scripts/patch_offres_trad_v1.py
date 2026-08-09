#!/usr/bin/env python3
"""
patch_offres_trad_v1.py — Les offres traduites PAR L'APP, plus par Safari.

POURQUOI : le traducteur de Safari peint des boites blanches derriere les
segments traduits sur fond sombre (constate sur capture) — illisible, et
hors de portee de notre CSS. La solution est de traduire les offres dans
Yorbity meme : titre + debut de description, via Ollama, dans la langue de
l'interface, avec cache SQLite. Plus besoin du traducteur du navigateur.

CE QUE FAIT LE PATCH :
  1. traduction.py : ajoute traduire_vers(texte, lang, model) — comme
     traduire() mais sans supposer que la source est le francais (les
     offres sont en allemand/anglais), avec les memes garde-fous et le
     meme cache. Ajoute aussi le parametre model (les offres utilisent un
     petit modele rapide, OFFRES_MODEL, defaut llama3.2:3b).
  2. sources/registre.py : chaque offre servie est traduite (titre +
     ~600 premiers caracteres de la description) dans la langue de
     session ; le bandeau 🛂 (deja localise) est preserve tel quel.
     Le moindre pepin laisse l'offre dans sa langue d'origine — jamais
     de page cassee.

LATENCE, honnetement : premiere consultation d'une page d'offres dans une
langue = quelques secondes par offre (petit modele), puis tout sort du
cache. Le reste de la description n'est pas traduit (marque […]) — le
lien officiel donne toujours l'annonce complete.

Idempotent. Sauvegardes .bak. Syntaxe verifiee, restauration si casse.
Usage : python scripts/patch_offres_trad_v1.py [--dry]
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
# 1. traduction.py
# =========================================================================== #
T1 = "def _appel_ollama(texte, lang):"
R_T1 = "def _appel_ollama(texte, lang, model=None):"

T2 = '            "model": MODEL, "prompt": prompt, "stream": False,'
R_T2 = '            "model": model or MODEL, "prompt": prompt, "stream": False,'

T3 = "def traduire(texte, lang):"
R_T3 = '''def _generer(prompt, model=None):
    """Appel Ollama brut (patch_offres) : prompt libre, modele au choix."""
    try:
        payload = json.dumps({
            "model": model or MODEL, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.2}
        }).encode()
        req = urllib.request.Request(f"{OLLAMA}/api/generate", data=payload,
                                     headers={"Content-Type": "application/json"})
        rep = json.loads(urllib.request.urlopen(req, timeout=120).read())
        return rep.get("response", "").strip()
    except Exception:
        return None


def traduire_vers(texte, lang, model=None):
    """Comme traduire(), mais SANS supposer que la source est le francais
    (patch_offres) : sert aux offres d'emploi (allemand/anglais -> langue
    de l'interface, y compris le francais). Meme cache, memes garde-fous."""
    if not texte or not lang:
        return texte
    cache = _du_cache(texte, lang)
    if cache is not None:
        return cache
    langue = nom_langue(lang) or ("français" if lang == "fr" else None)
    if not langue:
        return texte
    prompt = (f"Traduis le texte suivant vers le {langue}. "
              f"Réponds UNIQUEMENT dans cette langue ({langue}). "
              f"Garde le même sens, les montants, noms propres et sigles. "
              f"Aucun commentaire, uniquement la traduction.\\n\\nTexte : {texte}")
    trad = _generer(prompt, model)
    if trad and trad.strip() != texte.strip() and not _semble_francais(trad, lang):
        _au_cache(texte, lang, trad)
        return trad
    return texte


def traduire(texte, lang):'''

T4 = "    trad = _appel_ollama(texte, lang)"
R_T4 = "    trad = _appel_ollama(texte, lang)  # (modele principal)"


def patch_traduction() -> None:
    p = RACINE / "app" / "api" / "traduction.py"
    src = p.read_text(encoding="utf-8")
    if "traduire_vers" in src:
        resultats.append("= traduction.py : traduire_vers deja present")
        return
    if "nom_langue" not in src:
        resultats.append("? traduction.py : fixpack v1 absent — lance d'abord "
                         "patch_fixpack_v1.py")
        return
    n = 0
    for a, r in ((T1, R_T1), (T2, R_T2), (T3, R_T3), (T4, R_T4)):
        if a in src:
            src = src.replace(a, r, 1); n += 1
        else:
            resultats.append(f"? traduction.py : ancre absente ({a[:44]!r}…)")
    if n == 4:
        ecrire(p, src, n)
    else:
        resultats.append(f"? traduction.py : {n}/4 — RIEN ecrit")


# =========================================================================== #
# 2. sources/registre.py
# =========================================================================== #
A_DEF = '''def collecter_page(
    destination: str,'''
R_DEF = '''_EXTRAIT_TRAD = 600


def _traduire_offre(od: dict, lang: str) -> None:
    """Traduit titre + debut d'extrait dans la langue de l'interface via le
    pipeline maison (cache SQLite, petit modele rapide OFFRES_MODEL) —
    patch_offres. Le bandeau 🛂 (deja localise) est preserve. Le moindre
    pepin laisse l'offre telle quelle."""
    try:
        if not lang:
            try:
                import streamlit as st
                lang = st.session_state.get("lang", "")
            except Exception:
                return
        if not lang or lang == od.get("langue_source"):
            return
        import os

        import traduction
        if not hasattr(traduction, "traduire_vers"):
            return
        modele = os.environ.get("OFFRES_MODEL", "llama3.2:3b")
        titre = od.get("titre") or ""
        if titre:
            od["titre"] = traduction.traduire_vers(titre, lang, modele)
        ex = od.get("extrait") or ""
        if not ex:
            return
        pre = ""
        if ex.startswith("🛂"):
            coupe = ex.find("\\n\\n")
            if coupe > 0:
                pre, ex = ex[:coupe + 2], ex[coupe + 2:]
        tete, reste = ex[:_EXTRAIT_TRAD], ex[_EXTRAIT_TRAD:]
        od["extrait"] = (pre + traduction.traduire_vers(tete, lang, modele)
                         + ("\\n\\n[…]" if reste else ""))
    except Exception:
        pass


def collecter_page(
    destination: str,'''

A_APPEND = '''            od = o.to_dict()
            od["lien_accessible"] = accessible
            offres.append(od)'''
R_APPEND = '''            od = o.to_dict()
            od["lien_accessible"] = accessible
            _traduire_offre(od, lang)          # patch_offres
            offres.append(od)'''


def patch_registre() -> None:
    p = RACINE / "app" / "api" / "sources" / "registre.py"
    src = p.read_text(encoding="utf-8")
    if "_traduire_offre" in src:
        resultats.append("= registre.py : traduction des offres deja en place")
        return
    n = 0
    for a, r in ((A_DEF, R_DEF), (A_APPEND, R_APPEND)):
        if a in src:
            src = src.replace(a, r, 1); n += 1
        else:
            resultats.append(f"? registre.py : ancre absente ({a[:44]!r}…)")
    if n == 2:
        ecrire(p, src, n)
    else:
        resultats.append(f"? registre.py : {n}/2 — RIEN ecrit")


def main() -> None:
    if DRY:
        print(">>> DRY-RUN\n")
    patch_traduction()
    patch_registre()
    print()
    for r in resultats:
        print(" ", r)
    if any(r.startswith("x") for r in resultats):
        sys.exit(1)
    if any(r.startswith("?") for r in resultats):
        sys.exit(2)
    print("\nFINI — vide le cache offres, relance, et dans Safari :")
    print("  icone 🌐 -> Afficher l'original (le traducteur Safari devient inutile).")


if __name__ == "__main__":
    main()
