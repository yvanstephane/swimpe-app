#!/usr/bin/env python3
"""
traduire_i18n.py — Traduit l'INTERFACE dans n'importe quelle langue, via
ton Ollama local, en surcouches JSON relisibles.

    python scripts/traduire_i18n.py --langue de
    python scripts/traduire_i18n.py --langue de --modele llama3.3:70b-instruct-q4_K_M
    python scripts/traduire_i18n.py --langue es --force

Fonctionnement :
  1. S'assure que i18n.py charge les surcouches data/i18n/<lg>.json
     (installe le chargeur v2 si besoin, avec sauvegarde .bak).
  2. Importe T, repere chaque cle SANS traduction dans la langue cible
     (heuristique : valeur identique au francais = non traduite ; les
     traductions deja presentes dans le code ou la surcouche sont gardees).
  3. Traduit via Ollama (texte simple ET listes, element par element),
     en preservant emojis et champs {entre_accolades}.
  4. Ecrit/complete data/i18n/<lg>.json. Relance l'app pour voir.

Le repli francais de i18n.py reste : une cle non traduite ne plantera
JAMAIS, elle s'affiche en francais en attendant.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "app" / "api"))

OLLAMA = "http://localhost:11434/api/generate"

NOMS_LANGUES = {
    "de": "allemand", "en": "anglais", "es": "espagnol", "pt": "portugais",
    "zh": "chinois simplifié", "ar": "arabe", "it": "italien",
    "nl": "néerlandais", "tr": "turc", "ru": "russe", "wo": "wolof",
    "sw": "swahili",
}

# ---------------------------------------------------------------------------- #
# 1. Chargeur de surcouches dans i18n.py (v2 du bloc de repli)
# ---------------------------------------------------------------------------- #
BLOC_V2 = '''

# --- Surcouches + repli de langue UNIVERSEL (traduire_i18n v2) ----------------
# 1) data/i18n/<lg>.json surcharge T (traductions generees ou corrigees a la
#    main) ; 2) toute langue de LANGUES absente d'une entree herite du
#    francais. Ajouter une langue ne peut plus faire planter l'application.
def _charger_surcouches():
    import json as _json
    from pathlib import Path as _P
    for _base in (_P("data") / "i18n",
                  _P(__file__).resolve().parents[2] / "data" / "i18n"):
        try:
            fichiers = sorted(_base.glob("*.json"))
        except Exception:
            continue
        for _f in fichiers:
            try:
                _lg = _f.stem
                for _cle, _val in _json.loads(
                        _f.read_text(encoding="utf-8")).items():
                    if _cle in T and isinstance(T[_cle], dict):
                        T[_cle][_lg] = _val
            except Exception:
                pass
        if fichiers:
            break


def _completer_langues():
    try:
        for _val in T.values():
            if isinstance(_val, dict) and "fr" in _val:
                for _lg in LANGUES:
                    _val.setdefault(_lg, _val["fr"])
    except Exception:
        pass


_charger_surcouches()
_completer_langues()
'''

ANCIEN_DEBUT = "# --- Repli de langue UNIVERSEL (patch_langue_dossier) "


def assurer_chargeur() -> None:
    p = RACINE / "app" / "api" / "i18n.py"
    src = p.read_text(encoding="utf-8")
    if "_charger_surcouches" in src:
        print("= i18n.py : chargeur de surcouches deja en place")
        return
    bak = p.with_suffix(f".py.bak-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(p, bak)
    i = src.find(ANCIEN_DEBUT)
    if i >= 0:
        # remplace l'ancien bloc (il court jusqu'a la fin du fichier)
        src = src[:i].rstrip() + "\n" + BLOC_V2
    else:
        src = src.rstrip() + "\n" + BLOC_V2
    ast.parse(src)
    p.write_text(src, encoding="utf-8")
    print(f"v i18n.py : chargeur v2 installe ({bak.name})")


# ---------------------------------------------------------------------------- #
# 2. Traduction via Ollama
# ---------------------------------------------------------------------------- #
def traduire_texte(texte: str, langue: str, modele: str) -> str | None:
    import requests
    nom = NOMS_LANGUES.get(langue, langue)
    prompt = (
        f"Traduis en {nom} le texte d'interface suivant, dans un registre "
        "chaleureux et professionnel (tutoiement si la langue le permet).\n"
        "Conserve TEL QUEL : les emojis, et tout element entre accolades "
        "comme {pays} ou {prix}.\n"
        "Reponds UNIQUEMENT par la traduction, sans guillemets ni commentaire.\n\n"
        f"Texte : {texte}"
    )
    try:
        r = requests.post(OLLAMA, timeout=180, json={
            "model": modele, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.1, "num_predict": 400}})
        r.raise_for_status()
        out = (r.json().get("response") or "").strip()
        out = re.sub(r'^["\'«»\s]+|["\'«»\s]+$', "", out)
        out = out.splitlines()[0].strip() if out else ""
        return out or None
    except Exception as e:
        print(f"    ! Ollama : {e}")
        return None


def traduire_valeur(val, langue: str, modele: str):
    """str -> str traduit ; list -> liste traduite element par element
    (longueur preservee, sinon on renonce)."""
    if isinstance(val, str):
        return traduire_texte(val, langue, modele)
    if isinstance(val, list):
        out = []
        for elem in val:
            t = traduire_texte(str(elem), langue, modele)
            if t is None:
                return None
            out.append(t)
        return out if len(out) == len(val) else None
    return None


# ---------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("langues", nargs="*",
                    help="codes langue (de es pt ...) ; vide = --langue")
    ap.add_argument("--langue", default="de")
    ap.add_argument("--toutes", action="store_true",
                    help="toutes les langues de LANGUES sauf fr")
    ap.add_argument("--modele", default="llama3.2:3b",
                    help="ex. llama3.3:70b-instruct-q4_K_M pour la qualite")
    ap.add_argument("--force", action="store_true",
                    help="retraduit meme si la surcouche a deja la cle")
    args = ap.parse_args()

    print("traduire_i18n v2 — multi-langues (--toutes, positionnels)")  # VERSION_TRI
    assurer_chargeur()

    import importlib
    import i18n
    importlib.reload(i18n)
    T = i18n.T

    if args.toutes:
        cibles = [c for c in i18n.LANGUES if c != "fr"]
    elif args.langues:
        cibles = [c.strip().lower() for c in args.langues]
    else:
        cibles = [args.langue.strip().lower()]

    for lg in cibles:
        print("\n" + "=" * 60 + f"\nLANGUE : {lg}\n" + "=" * 60)
        _traiter_langue(lg, T, args)


def _traiter_langue(lg, T, args):

    dossier = RACINE / "data" / "i18n"
    dossier.mkdir(parents=True, exist_ok=True)
    fichier = dossier / f"{lg}.json"
    surcouche: dict = {}
    if fichier.exists():
        surcouche = json.loads(fichier.read_text(encoding="utf-8"))

    a_traduire = []
    for cle, val in T.items():
        if not (isinstance(val, dict) and "fr" in val):
            continue
        if not args.force and cle in surcouche:
            continue
        # deja traduit dans le code (valeur differente du francais) ?
        if not args.force and val.get(lg) not in (None, val["fr"]):
            continue
        a_traduire.append((cle, val["fr"]))

    print(f"\n{len(a_traduire)} cle(s) a traduire en {lg} "
          f"(modele {args.modele})\n")
    faits = 0
    for cle, fr in a_traduire:
        apercu = fr if isinstance(fr, str) else " | ".join(map(str, fr[:3]))
        print(f"  {cle:24} {apercu[:52]}")
        t = traduire_valeur(fr, lg, args.modele)
        if t is None:
            print("    -> echec, cle sautee (repli francais a l'ecran)")
            continue
        surcouche[cle] = t
        faits += 1
        fichier.write_text(json.dumps(surcouche, ensure_ascii=False,
                                      indent=1, sort_keys=True),
                           encoding="utf-8")   # sauvegarde incrementale
    print(f"\n{faits}/{len(a_traduire)} traduites -> {fichier.relative_to(RACINE)}")
    print("Corrige librement ce JSON a la main si besoin, puis relance l'app.")


if __name__ == "__main__":
    main()
