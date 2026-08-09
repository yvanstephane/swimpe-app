#!/usr/bin/env python3
"""
patch_finitions.py — Quatre finitions apres captures d'ecran.

  1. HERO PROFESSIONNEL : les trois elements (prix, accompagnement,
     contact) etaient des pilules collees de largeurs disparates.
     Ils passent en RANGEE FLEX : espacement constant (gap .7rem),
     coins arrondis 10px, ombre discrete, retour a la ligne propre
     sur mobile. Grammaire visuelle « cabinet ».
  2. BADGES RETIRES : la rangee « Metier specialise / Choisir… » sous le
     hero n'apportait rien (« Choisir… » = placeholder du niveau, grise
     pour les metiers).
  3. LIEN DES OFFRES ALLEMANDES : la route jobdetail/{refnr} de la BA
     redirige vers l'accueil Jobsuche (constate le 2026-07-10). La page
     BA indique elle-meme que la Referenznummer est cherchable -> chaque
     offre pointe desormais vers la recherche par reference, qui atterrit
     sur le poste exact :
         https://www.arbeitsagentur.de/jobsuche/suche?was=<refnr>
  4. ALLEMAND SELECTIONNABLE : "de" ajoute a LANGUES + traduction de la
     cle 'accompagne'. Les autres cles retombent sur le francais tant que
     T n'a pas de colonne "de" (autotrad peut prendre le relais).

Idempotent. Sauvegardes .bak. Syntaxe verifiee, restauration si casse.
Usage : python scripts/patch_finitions.py [--dry]
"""
from __future__ import annotations

import ast
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DRY = "--dry" in sys.argv
HORO = datetime.now().strftime("%Y%m%d-%H%M%S")
MARQUE = "patch_finitions"

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
# ui.py — 1. hero flex + 2. badges
# =========================================================================== #
A_HERO = (
    "  <span class='prix'>{t(\"start_from\", LG)} {_prix_banniere}</span>\n"
    "  <a href='{_url_acc}' target='_blank' style='text-decoration:none; "
    "margin-left:.6rem; background:#e9b949; color:#1f2937; "
    "padding:.4rem .9rem; border-radius:999px; font-weight:700; "
    "display:inline-block;'>{t('accompagne', LG)} "
    "{nom_pays(d['nom'], LG)} →</a>\n"
    "  <a href='{_url_contact}' target='_blank' style='text-decoration:none; "
    "margin-left:.5rem; background:#ffffff; color:#1f2937; "
    "padding:.4rem .9rem; border-radius:999px; font-weight:700; "
    "display:inline-block;'>{t('form_titre', LG).split('—')[0].strip()} →</a>"
)

R_HERO = (
    "  <div style='display:flex; flex-wrap:wrap; align-items:center; "
    "gap:.7rem; margin-top:1.15rem;'>  <!-- patch_finitions -->\n"
    "    <span class='prix' style='margin:0;'>"
    "{t(\"start_from\", LG)} {_prix_banniere}</span>\n"
    "    <a href='{_url_acc}' target='_blank' style='text-decoration:none; "
    "background:#e9b949; color:#1f2937; padding:.55rem 1.1rem; "
    "border-radius:10px; font-weight:600; display:inline-block; "
    "box-shadow:0 1px 3px rgba(0,0,0,.18);'>{t('accompagne', LG)} "
    "{nom_pays(d['nom'], LG)} →</a>\n"
    "    <a href='{_url_contact}' target='_blank' style='text-decoration:none; "
    "background:rgba(255,255,255,.94); color:#1f2937; "
    "padding:.55rem 1.1rem; border-radius:10px; font-weight:600; "
    "display:inline-block; box-shadow:0 1px 3px rgba(0,0,0,.18);'>"
    "{t('form_titre', LG).split('—')[0].strip()} →</a>\n"
    "  </div>"
)

A_BADGES = '''    st.markdown(
        f"<span class='badge'>{type_}</span><span class='badge'>{niveau}</span>"
        + (f"<span class='badge'>{domaine}</span>" if domaine_c != "Tous les domaines" else ""),
        unsafe_allow_html=True)'''
R_BADGES = ("    # Badges type/niveau retires (patch_finitions) : redondants "
            "avec les selecteurs.")


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
    if A_HERO in src:
        src = src.replace(A_HERO, R_HERO, 1); n += 1
    else:
        resultats.append("? ui.py : bloc hero introuvable (mise en page non changee)")
    if A_BADGES in src:
        src = src.replace(A_BADGES, R_BADGES, 1); n += 1
    else:
        resultats.append("? ui.py : ligne badges introuvable")
    if n:
        ecrire(p, src, n)


# =========================================================================== #
# i18n.py — allemand
# =========================================================================== #
def patch_i18n() -> None:
    p = RACINE / "app" / "api" / "i18n.py"
    if not p.exists():
        resultats.append("- i18n.py introuvable")
        return
    src = p.read_text(encoding="utf-8")
    n = 0

    if '"de"' not in src.split("LANGUES", 1)[-1][:400]:
        m = re.search(r"LANGUES\s*=\s*\{", src)
        if m:
            src = src[:m.end()] + '\n "de": "Deutsch",' + src[m.end():]
            n += 1
        else:
            resultats.append("? i18n.py : dict LANGUES introuvable — 'de' non ajoute")
    else:
        resultats.append("= i18n.py : 'de' deja dans LANGUES")

    a = '"zh":"🤝 我们陪你推进你的项目 —", "ar":"🤝 نرافقك في مشروعك —"},'
    if '"de":"🤝 Wir begleiten' not in src:
        if a in src:
            src = src.replace(
                a,
                '"de":"🤝 Wir begleiten dich bei deinem Projekt —",\n   ' + a, 1)
            n += 1
        else:
            resultats.append("? i18n.py : cle 'accompagne' non trouvee pour le de")

    if n:
        ecrire(p, src, n)


# =========================================================================== #
# sources/mig_de.py — lien par reference
# =========================================================================== #
A_URL = ('''        url = (a.get("externeUrl")
               or f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{refnr}")''')
R_URL = ('''        # jobdetail/{refnr} redirige vers l'accueil Jobsuche (constate
        # 2026-07-10). La BA indique que la Referenznummer est cherchable :
        # la recherche par reference atterrit sur le poste exact.
        url = (a.get("externeUrl")
               or "https://www.arbeitsagentur.de/jobsuche/suche?was="
               + _up.quote(refnr))''')


def patch_mig() -> None:
    p = RACINE / "app" / "api" / "sources" / "mig_de.py"
    if not p.exists():
        resultats.append("- mig_de.py introuvable")
        return
    src = p.read_text(encoding="utf-8")
    if "jobsuche/suche?was=" in src:
        resultats.append("= mig_de.py : lien par reference deja en place")
        return
    if A_URL not in src:
        resultats.append("? mig_de.py : ancre url introuvable")
        return
    src = src.replace(A_URL, R_URL, 1)
    if "import urllib.parse as _up" not in src:
        src = src.replace("import requests",
                          "import urllib.parse as _up\n\nimport requests", 1)
    ecrire(p, src, 1)


# =========================================================================== #
def main() -> None:
    if DRY:
        print(">>> DRY-RUN\n")
    patch_ui()
    patch_i18n()
    patch_mig()
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
