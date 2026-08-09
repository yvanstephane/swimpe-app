#!/usr/bin/env python3
"""
patch_langue_dossier.py — Deux regles, posees une bonne fois pour toutes.

1. LANGUE : REPLI UNIVERSEL (fin du KeyError: 'de', et de tous les suivants)
   Le plantage venait de T["types"]["de"] : le dictionnaire T n'a pas de
   colonne allemande. Corriger ligne par ligne serait sans fin.
   La technique definitive : au chargement de i18n.py, chaque entree de T
   est completee — toute langue de LANGUES absente d'une entree HERITE DU
   FRANCAIS. Ajouter une langue ne peut plus jamais faire planter l'app ;
   les textes non traduits s'affichent en francais en attendant.

2. DOSSIER UNIQUE : un compte = UN dossier. dossiers.creer() refuse un
   second dossier avec un message affiche a l'ecran (pas d'echec muet) ;
   les candidatures du client se rattachent a ce dossier.
   `autorise_tiers=True` (ecrans admin) passe outre.

3. VALIDATION DE NOM RETIREE (demande) : l'inscription n'exige plus
   prenom+nom ; la normalisation des espaces est conservee, la mention
   sous le champ aussi (informative). Si patch_identite n'avait pas ete
   applique, cette etape dit simplement « deja ».

Idempotent. Sauvegardes .bak. Syntaxe verifiee, restauration si casse.
Usage : python scripts/patch_langue_dossier.py [--dry]
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


def ecrire(p: Path, contenu: str, n: int) -> bool:
    if DRY:
        resultats.append(f"~ {p.name} : {n} retouche(s) [DRY-RUN]")
        return True
    bak = p.with_suffix(p.suffix + f".bak-{HORO}")
    shutil.copy2(p, bak)
    p.write_text(contenu, encoding="utf-8")
    try:
        ast.parse(contenu)
    except SyntaxError as e:
        shutil.copy2(bak, p)
        resultats.append(f"x {p.name} : syntaxe cassee l.{e.lineno} — restaure")
        return False
    resultats.append(f"v {p.name} : {n} retouche(s) ({bak.name})")
    return True


# =========================================================================== #
# 1. i18n.py — repli universel
# =========================================================================== #
BLOC_REPLI = '''

# --- Repli de langue UNIVERSEL (patch_langue_dossier) -------------------------
# Toute langue presente dans LANGUES mais absente d'une entree de T herite
# du francais. Ajouter une langue au selecteur ne peut plus faire planter
# l'application : les textes non traduits s'affichent en francais.
def _completer_langues():
    try:
        for _val in T.values():
            if isinstance(_val, dict) and "fr" in _val:
                for _lg in LANGUES:
                    _val.setdefault(_lg, _val["fr"])
    except Exception:
        pass


_completer_langues()
'''


def patch_i18n() -> None:
    p = RACINE / "app" / "api" / "i18n.py"
    if not p.exists():
        resultats.append("- i18n.py introuvable")
        return
    src = p.read_text(encoding="utf-8")
    if "_completer_langues" in src:
        resultats.append("= i18n.py : repli universel deja en place")
        return
    src = src.rstrip() + "\n" + BLOC_REPLI
    ecrire(p, src, 1)


# =========================================================================== #
# 2. dossiers.py — dossier unique
# Deux etats possibles selon que patch_identite a ete applique : on remplace
# l'un OU l'autre par la version canonique v3.
# =========================================================================== #
CREER_ORIGINAL = '''def creer(user_id, service, destination):
    init_db()
    auj = datetime.date.today().isoformat()
    con = sqlite3.connect(DB)
    con.execute("INSERT INTO dossiers(user_id,service,destination,cree_le,maj_le) "
                "VALUES(?,?,?,?,?)", (user_id, service, destination, auj, auj))
    con.commit(); con.close()'''

CREER_V3 = '''def creer(user_id, service, destination, beneficiaire=None,
          autorise_tiers=False):
    """Cree LE dossier du compte — un seul dossier par client
    (patch_langue_dossier). Les candidatures du client s'y rattachent.
    `autorise_tiers=True` (ecrans admin) passe outre.
    Retourne (True, "") ou (False, message). Le refus est aussi affiche a
    l'ecran quand Streamlit est disponible : pas d'echec silencieux."""
    init_db()
    con = sqlite3.connect(DB)
    try:
        row = con.execute("SELECT nom FROM users WHERE id=?",
                          (user_id,)).fetchone()
        if not row:
            return _refus("Compte introuvable.")
        if not autorise_tiers:
            deja = con.execute(
                "SELECT id, service, destination FROM dossiers "
                "WHERE user_id=? ORDER BY id LIMIT 1", (user_id,)).fetchone()
            if deja:
                return _refus(
                    "Un seul dossier par compte : le tien est le "
                    f"n°{deja[0]} ({deja[1]} → {deja[2]}). Tes candidatures "
                    "s'y rattachent — contacte-nous pour le faire evoluer.")
        auj = datetime.date.today().isoformat()
        con.execute("INSERT INTO dossiers(user_id,service,destination,cree_le,maj_le) "
                    "VALUES(?,?,?,?,?)", (user_id, service, destination, auj, auj))
        con.commit()
        return True, ""
    finally:
        con.close()


def _refus(msg):
    try:
        import streamlit as _st
        _st.warning("🗂 " + msg)
    except Exception:
        pass
    return False, msg'''


def patch_dossiers() -> None:
    p = RACINE / "app" / "api" / "dossiers.py"
    if not p.exists():
        resultats.append("- dossiers.py introuvable")
        return
    src = p.read_text(encoding="utf-8")
    if "Un seul dossier par compte" in src:
        resultats.append("= dossiers.py : regle du dossier unique deja en place")
        return

    if CREER_ORIGINAL in src:
        src = src.replace(CREER_ORIGINAL, CREER_V3, 1)
        ecrire(p, src, 1)
        return

    # etat patch_identite : on remplace toute la fonction creer() par v3,
    # bornee structurellement (de "def creer(" au prochain "def " colonne 0).
    i = src.find("def creer(user_id, service, destination, beneficiaire=None")
    if i < 0:
        resultats.append("? dossiers.py : aucune forme connue de creer() — "
                         "envoie : sed -n '38,90p' app/api/dossiers.py")
        return
    j = src.find("\ndef ", i + 1)
    if j < 0:
        j = len(src)                     # creer() est la derniere fonction
    src = src[:i] + CREER_V3 + src[j:]
    ecrire(p, src, 1)


# =========================================================================== #
# 3. auth.py — retrait de la validation stricte du nom (si presente)
# =========================================================================== #
BLOC_VALIDATION = '''
    # Abonnement PERSONNEL : le nom du compte est un nom legal complet
    # (patch_identite). Les dossiers ne peuvent etre ouverts qu'a ce nom.
    try:
        import identite
        ok_nom, err_nom = identite.valider_nom_complet(nom)
        if not ok_nom:
            return False, err_nom
    except ImportError:
        pass'''


def patch_auth() -> None:
    p = RACINE / "app" / "api" / "auth.py"
    if not p.exists():
        resultats.append("- auth.py introuvable")
        return
    src = p.read_text(encoding="utf-8")
    if BLOC_VALIDATION not in src:
        resultats.append("= auth.py : pas de validation stricte a retirer")
        return
    src = src.replace(BLOC_VALIDATION, "", 1)
    ecrire(p, src, 1)


# =========================================================================== #
def main() -> None:
    if DRY:
        print(">>> DRY-RUN\n")
    patch_i18n()
    patch_dossiers()
    patch_auth()
    print()
    for r in resultats:
        print(" ", r)
    if any(r.startswith("x") for r in resultats):
        sys.exit(1)
    if any(r.startswith("?") for r in resultats):
        print("\nATTENTION : certaines retouches sautees (voir ?).")
        sys.exit(2)
    print("\nFINI — pkill -f streamlit ; puis : yorbity")


if __name__ == "__main__":
    main()
