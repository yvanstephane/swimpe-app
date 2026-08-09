#!/usr/bin/env python3
"""
patch_jobboard3.py — Finitions demandees apres capture d'ecran.

  1. FORMULAIRE RETIRE de la page principale : il vit desormais derriere
     les liens (?page=contact et ?page=accompagnement). La section
     « Nous contacter » (WhatsApp / e-mail) reste.
     Le retrait est STRUCTUREL : on part de l'ancre du titre, on verifie
     que `with st.form(` suit, on consomme le corps du formulaire par son
     indentation, et on emporte la ligne de disclaimer (« garantir une
     admission ») qui l'accompagne — le disclaimer vit deja sur les pages
     dediees.
  2. DOUBLE 🤝 corrige : la valeur i18n contient l'emoji ; les liens ne le
     prefixent plus.
  3. COULEURS des deux boutons du bas : `type="primary"` (accent du theme)
     pour l'accompagnement, `secondary` pour le contact — natif Streamlit,
     contrairement aux styles inline que link_button ignore.
  4. CTA des offres (jobs_api) : « Remplis le formulaire en bas de page »
     pointait vers un formulaire qui n'existe plus -> nouveau message
     orientant vers le lien « Parle-nous de ton projet ».

Idempotent. Sauvegardes .bak. Syntaxe verifiee, restauration si casse.
Usage : python scripts/patch_jobboard3.py [--dry]
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
MARQUE = "patch_jobboard3"

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
# 2a. hero : plus de 🤝 prefixe (l'emoji vient de i18n)
A_HERO = ("display:inline-block;'>🤝 {t('accompagne', LG)} "
          "{nom_pays(d['nom'], LG)} →</a>")
R_HERO = ("display:inline-block;'>{t('accompagne', LG)} "
          "{nom_pays(d['nom'], LG)} →</a>")

# 2b+3. bas de page : plus de prefixe, couleurs natives distinctes
A_BAS = ('''    _cA, _cB = st.columns(2)
    _cA.link_button("🤝 " + t("accompagne", LG) + " " + nom_pays(d["nom"], LG) + " →",
                    _url_acc, use_container_width=True)
    _cB.link_button(t("form_titre", LG).split("—")[0].strip() + " →",
                    _url_contact, use_container_width=True)''')
R_BAS = ('''    _cA, _cB = st.columns(2)  # patch_jobboard3
    _cA.link_button(t("accompagne", LG) + " " + nom_pays(d["nom"], LG) + " →",
                    _url_acc, use_container_width=True, type="primary")
    _cB.link_button(t("form_titre", LG).split("—")[0].strip() + " →",
                    _url_contact, use_container_width=True, type="secondary")''')

# 1. formulaire : ancre de depart
A_FORM = '    st.markdown("#### " + t("form_titre", LG))'
R_FORM = ("    # Formulaire retire de la page principale (patch_jobboard3) :\n"
          "    # il vit sur ?page=contact et ?page=accompagnement (liens ci-dessus).")


def retirer_formulaire(src: str) -> str | None:
    """Retrait structurel du bloc formulaire PRINCIPAL, disclaimer compris.

    Piege evite : le routeur des pages dediees contient la MEME ancre
    form_titre, avec son propre formulaire (st.form("lead_page_dediee"))
    qu'il faut GARDER. On discrimine sur le nom exact st.form("lead")."""
    pos = 0
    while True:
        i = src.find(A_FORM, pos)
        if i < 0:
            return None
        lignes = src[i:].splitlines(keepends=True)
        tete = "".join(lignes[:4])
        if 'with st.form("lead")' in tete:
            break                                 # la bonne occurrence
        pos = i + len(A_FORM)                     # celle du routeur : on passe

    # trouve `with st.form("lead"):` puis consomme son corps (indent > 4)
    fin = None
    dans_form = False
    for k, l in enumerate(lignes):
        d = l.rstrip("\n")
        if not dans_form:
            if d.lstrip().startswith('with st.form("lead")'):
                dans_form = True
            continue
        if not d.strip():
            continue
        indent = len(d) - len(d.lstrip())
        if indent <= 4:                     # sorti du corps du formulaire
            fin = k
            break
    if fin is None:
        return None

    # emporte le disclaimer s'il suit immediatement
    while fin < len(lignes):
        d = lignes[fin].strip()
        if not d:
            fin += 1
            continue
        if "garantir" in d and d.startswith("st."):
            fin += 1
        break

    bloc = "".join(lignes[:fin])
    if "form_submit_button" not in bloc or "INSERT INTO leads" not in bloc:
        return None                          # garde-fou : pas le bon bloc
    if "lead_page_dediee" in bloc:
        return None                          # garde-fou : jamais le routeur
    return src[:i] + R_FORM + "\n" + src[i + len(bloc):]


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
        resultats.append("? ui.py : ancre hero absente (double 🤝 non corrige)")
    if A_BAS in src:
        src = src.replace(A_BAS, R_BAS, 1); n += 1
    else:
        resultats.append("? ui.py : ancre bas-de-page absente")

    nouveau = retirer_formulaire(src)
    if nouveau is None:
        resultats.append("? ui.py : bloc formulaire non identifie — NON retire")
    else:
        src = nouveau; n += 1

    if n == 0:
        resultats.append("? ui.py : aucune retouche applicable")
        return
    ecrire(p, src, n)


# =========================================================================== #
# jobs_api.py — message du CTA des offres
# =========================================================================== #
A_CTA = ('tr("Offre selectionnee. Remplis le formulaire en bas '
         '"\n                             "de page : la reference y sera reprise.")')
R_CTA = ('tr("Offre sélectionnée — clique sur « Parle-nous de ton projet » '
         '"\n                             "et indique cette référence.")')


def patch_jobs_api() -> None:
    p = RACINE / "app" / "api" / "jobs_api.py"
    if not p.exists():
        resultats.append("- jobs_api.py introuvable")
        return
    src = p.read_text(encoding="utf-8")
    if "et indique cette référence" in src:
        resultats.append("= jobs_api.py : CTA deja corrige")
        return
    if A_CTA not in src:
        resultats.append("? jobs_api.py : ancre CTA absente — verifie "
                         "grep -n 'Remplis le formulaire' app/api/jobs_api.py")
        return
    src = src.replace(A_CTA, R_CTA, 1)
    ecrire(p, src, 1)


# =========================================================================== #
def main() -> None:
    if DRY:
        print(">>> DRY-RUN\n")
    patch_ui()
    patch_jobs_api()
    print()
    for r in resultats:
        print(" ", r)
    if any(r.startswith("x") for r in resultats):
        sys.exit(1)
    if any(r.startswith("?") for r in resultats):
        print("\nATTENTION : certaines retouches ont ete sautees (voir ?).")
        sys.exit(2)
    print("\nFINI — pkill -f streamlit ; puis : yorbity")


if __name__ == "__main__":
    main()
