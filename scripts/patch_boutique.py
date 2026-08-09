#!/usr/bin/env python3
"""
patch_boutique.py — Branche la boutique (Premium + services a la carte).

  1. ui.py : enregistre le catalogue SVC aupres de paiement + affiche
     l'ecran boutique pour un client connecte (avant l'ecran Premium).
     Ancre : `# ---------- Écran Premium ----------`.
  2. ui.py : CORRIGE LE PIEGE du retour de paiement —
        OFFRES.get(code, ("", 0, 30))[2]
     offrait 30 jours de Premium a TOUT code inconnu. Un service a la
     carte revenant par cette route aurait offert un mois de Premium.
     Desormais : jours = paiement.duree_jours(code) ; 0 jour = service,
     livre dans le dossier unique du client.
  3. espace.py : bouton « 🛠 Services & démarches » dans le bloc compte
     de la barre laterale (client connecte).
  4. devises.py : devises d'ORIGINE ajoutees (DZ, TN, GN, CD, NG, GH, KE)
     pour l'affichage du prix dans la monnaie du client.

Prerequis : app/api/paiement.py v2 (livre ensemble).
Idempotent. Sauvegardes .bak. Syntaxe verifiee, restauration si casse.
Usage : python scripts/patch_boutique.py [--dry]
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
MARQUE = "patch_boutique"

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
# ui.py
# =========================================================================== #
A_PREMIUM = "# ---------- Écran Premium ----------"
R_PREMIUM = '''# ---------- Boutique : Premium + services a la carte (patch_boutique) -------
import paiement as _paiement
_paiement.enregistrer_services(SVC)
if espace.user_connecte() and _paiement.ecran_boutique(st.session_state.user):
    st.stop()

# ---------- Écran Premium ----------'''

A_RETOUR = '''            jours = paiement.OFFRES.get(info["offre"], ("",0,30))[2]
            nouveau = auth.activer_premium(espace.user_connecte()["id"], jours)
            st.session_state.user["premium_jusqu"] = nouveau'''
R_RETOUR = '''            jours = paiement.duree_jours(info["offre"])  # patch_boutique :
            # 0 jour = service a la carte (l'ancien defaut offrait 30 j de
            # Premium a tout code inconnu).
            if jours > 0:
                nouveau = auth.activer_premium(espace.user_connecte()["id"], jours)
                st.session_state.user["premium_jusqu"] = nouveau
            else:
                st.success("✅ " + paiement.livrer_service(
                    info, espace.user_connecte()))'''


def patch_ui() -> None:
    p = RACINE / "app" / "api" / "ui.py"
    if not p.exists():
        resultats.append("- ui.py introuvable")
        return
    src = p.read_text(encoding="utf-8")
    if MARQUE in src:
        resultats.append("= ui.py : deja patche")
        return
    n = 0
    if A_PREMIUM in src:
        src = src.replace(A_PREMIUM, R_PREMIUM, 1); n += 1
    else:
        resultats.append("? ui.py : ancre 'Écran Premium' absente")
    if A_RETOUR in src:
        src = src.replace(A_RETOUR, R_RETOUR, 1); n += 1
    else:
        resultats.append("? ui.py : bloc retour de paiement non trouve a "
                         "l'identique (piege 30 j NON corrige)")
    if n:
        ecrire(p, src, n)


# =========================================================================== #
# espace.py — bouton dans le bloc compte
# =========================================================================== #
A_ESPACE = '''            if auth.est_premium(u):
                st.success(t("premium_actif", _lg()))
            else:
                st.caption(t("compte_gratuit", _lg()))'''
R_ESPACE = A_ESPACE + '''
            if st.button("🛠 Services & démarches", key="btn_boutique",
                         use_container_width=True):
                st.session_state.show_boutique = True
                st.rerun()'''


def patch_espace() -> None:
    p = RACINE / "app" / "api" / "espace.py"
    if not p.exists():
        resultats.append("- espace.py introuvable")
        return
    src = p.read_text(encoding="utf-8")
    if "show_boutique" in src:
        resultats.append("= espace.py : bouton deja en place")
        return
    if A_ESPACE not in src:
        resultats.append("? espace.py : bloc compte non trouve a l'identique")
        return
    src = src.replace(A_ESPACE, R_ESPACE, 1)
    ecrire(p, src, 1)


# =========================================================================== #
# devises.py — devises d'origine pour l'affichage
# =========================================================================== #
A_DEV = '    "MA": ("MAD", "DH", 10.8),'
R_DEV = '''    "MA": ("MAD", "DH", 10.8),
    "DZ": ("DZD", "DA", 148.0),      # dinar algerien — indicatif, volatil
    "TN": ("TND", "DT", 3.35),
    "GN": ("GNF", "FG", 9500.0),     # franc guineen — indicatif, volatil
    "CD": ("CDF", "FC", 2900.0),     # franc congolais — tres volatil
    "NG": ("NGN", "₦", 1650.0),
    "GH": ("GHS", "GH₵", 16.0),
    "KE": ("KES", "KSh", 140.0),'''


def patch_devises() -> None:
    p = RACINE / "app" / "api" / "devises.py"
    if not p.exists():
        resultats.append("- devises.py introuvable (affichage en FCFA)")
        return
    src = p.read_text(encoding="utf-8")
    if '"DZ"' in src:
        resultats.append("= devises.py : devises d'origine deja presentes")
        return
    if A_DEV not in src:
        resultats.append("? devises.py : ancre MA introuvable")
        return
    src = src.replace(A_DEV, R_DEV, 1)
    ecrire(p, src, 1)


# =========================================================================== #
def main() -> None:
    if DRY:
        print(">>> DRY-RUN\n")
    if not (RACINE / "app" / "api" / "paiement.py").exists():
        print("!! app/api/paiement.py manquant.")
        sys.exit(1)
    patch_ui()
    patch_espace()
    patch_devises()
    print()
    for r in resultats:
        print(" ", r)
    if any(r.startswith("x") for r in resultats):
        sys.exit(1)
    if any(r.startswith("?") for r in resultats):
        print("\nATTENTION : certaines retouches sautees (voir ?).")
        sys.exit(2)
    print("\nFINI — pkill -f streamlit ; puis relance.")


if __name__ == "__main__":
    main()
