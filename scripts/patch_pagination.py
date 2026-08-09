#!/usr/bin/env python3
"""
patch_pagination.py — Job board pagine + CTA d'accompagnement au bon endroit.

DEUX PROBLEMES RESOLUS

1) Seules 8 offres etaient visibles. Le flux Job Bank en rend ~100.
   On pagine, a COUT CONSTANT : le flux Atom (liste) est gratuit, seul le
   detail RDFa coute une requete HTTP par offre. On n'enrichit donc que les
   8 offres de la page affichee. Page 1 ou page 12 : meme cout (~10 s), puis
   cache 12 h par page.

2) Le bloc "On t'accompagne jusqu'en <pays>" est en bas de page. Avec des
   dizaines d'offres, personne ne le voit. Le remonter avant les offres,
   c'est vendre avant d'avoir montre la valeur — et une banniere haute
   existe deja.
   On place donc l'appel a l'action LA OU NAIT L'INTENTION :
     a) dans chaque offre, juste sous la reference : "Postuler avec notre
        accompagnement". C'est le moment ou l'utilisateur a vu une offre qui
        lui plait et se demande comment faire.
     b) un rappel compact d'une ligne apres la 3e offre.
   Le bloc complet reste en bas, inchange.

Le clic memorise l'offre dans st.session_state["offre_choisie"] :
    {"reference": "JOB-49877224", "titre": "...", "source": "jobbank_ca", ...}
Ton formulaire de contact peut le lire pour se pre-remplir :
    ref = (st.session_state.get("offre_choisie") or {}).get("reference", "")

Idempotent. Sauvegarde .bak. Verifie la syntaxe, restaure si casse.
Usage : python scripts/patch_pagination.py [--dry]
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
P = RACINE / "app" / "api" / "jobs_api.py"

# --------------------------------------------------------------------------- #
NOUVEAU = '''
# --- ajoute par patch_pagination.py ----------------------------------------
def _cle_page(dest_code, type_p, domaine):
    return f"page__{dest_code}__{type_p}__{domaine[:20]}"


def chercher_page(dest_code, type_projet, domaine="", page=1, par_page=None):
    """
    Une PAGE d'offres, toutes sources, + le total disponible.
    Cache 12 h par page (cle distincte de celle de chercher()).
    """
    par_page = par_page or MAX_OFFRES
    page = max(1, int(page))
    cle = f"page:{dest_code.upper()}:{type_projet}:{domaine[:20]}:{page}:{par_page}"

    cache = _cache_lire(cle)
    if isinstance(cache, dict):
        return cache.get("offres", []), cache.get("total", 0)

    try:
        from sources import registre
        offres, total = registre.collecter_page(
            dest_code, type_projet, mots_cles=domaine or None,
            page=page, par_page=par_page)
    except Exception as e:
        print("registre indisponible, repli Adzuna seul :", e)
        tout = _chercher_adzuna(dest_code, type_projet, domaine) or []
        total = len(tout)
        debut = (page - 1) * par_page
        offres = tout[debut:debut + par_page]

    offres = [o for o in offres if not _bruit(o)]
    try:
        _cache_ecrire(cle, dest_code.upper(), type_projet,
                      {"offres": offres, "total": total})
    except Exception as e:
        print("cache non ecrit :", e)
    return offres, total


def _cta_offre(o, tr, cle):
    """Appel a l'action AU MOMENT DE L'INTENTION : sous la reference."""
    if st.button("🤝 " + tr("Postuler avec notre accompagnement"),
                 key=cle, use_container_width=True):
        st.session_state["offre_choisie"] = {
            "reference": o.get("reference") or f"JOB-{o['id'][:10]}",
            "titre": o.get("titre", ""),
            "entreprise": o.get("entreprise", ""),
            "source": o.get("source", ""),
        }
        st.success("✅ " + tr("Offre selectionnee. Remplis le formulaire en bas "
                             "de page : la reference y sera reprise."))


def afficher(dest_code, tr, admin=False, code_orig="",
             types_live=("stage", "emploi", "metier"), poste="", domaine=""):
    """Affiche le job board pagine. Retourne le nb d'offres de la page."""
    try:
        import eligibilite
    except Exception:
        eligibilite = None
    try:
        import offres_sync
        _liens = offres_sync.liens_actifs()
        _desc = offres_sync.descriptions_actives()
    except Exception:
        _liens = False
        _desc = True

    TITRES = {"stage": "🧑‍💻 Stages en direct",
              "emploi": "💼 Emplois étudiants en direct",
              "metier": "🔧 Métiers spécialisés qui recrutent"}
    total_affiche = 0

    for type_p in types_live:
        titre = TITRES.get(type_p, type_p)

        if eligibilite is not None and code_orig:
            ok, note = eligibilite.autorise(dest_code, type_p, code_orig)
            if not ok:
                st.warning("🛂 " + tr("D'après nos informations, ce type d'offre "
                           "n'est pas ouvert aux ressortissants de ton pays "
                           "d'origine pour cette destination.")
                           + ((" " + tr(note)) if note else ""))
                continue
            if note:
                st.caption("🛂 " + tr(note))

        page_cle = _cle_page(dest_code, type_p, domaine)
        page = int(st.session_state.get(page_cle, 1))
        offres, total = chercher_page(dest_code, type_p, domaine, page)

        if poste:
            try:
                import recherche_poste
                offres = recherche_poste.filtre(offres, poste)
            except Exception:
                pass

        # Page devenue vide (filtre ou offres retirees) : revenir a la page 1.
        if not offres and page > 1:
            st.session_state[page_cle] = 1
            st.rerun()
        if not offres:
            continue

        st.markdown("#### " + tr(titre))

        par_page = MAX_OFFRES
        debut = (page - 1) * par_page + 1
        fin = debut + len(offres) - 1
        pages = max(1, -(-total // par_page))       # ceil
        if total > par_page:
            st.caption(f"{tr('Offres')} {debut}–{fin} {tr('sur environ')} {total}"
                       f"  ·  {tr('page')} {page}/{pages}")

        for i, o in enumerate(offres):
            total_affiche += 1
            entete = _toff(o["titre"]) if o["titre"] else tr("Offre")
            if o["entreprise"]:
                entete += f" — {o['entreprise']}"

            with st.expander(entete):
                if admin or _desc:
                    if o["lieu"]:
                        st.markdown("📍 " + _toff(o["lieu"]))
                    if o["salaire"]:
                        st.markdown("💶 " + o["salaire"])
                    if o["extrait"]:
                        st.write(_toff(o["extrait"]) + "…")
                    if o["date"]:
                        st.caption(tr("Publiée le") + " " + o["date"])
                else:
                    st.caption("🔒 " + tr("Description réservée — contacte-nous via le "
                                          "formulaire en bas de page."))

                st.caption("📌 " + tr("Référence à indiquer dans le formulaire :")
                           + " " + (o.get("reference") or f"JOB-{o['id'][:10]}"))

                _cta_offre(o, tr, f"cta_{type_p}_{page}_{o['id']}")

                if o.get("url") and (admin or (_liens and o.get("lien_accessible", True))):
                    st.link_button(
                        "🔗 " + (tr("Lien (admin)") if admin and not _liens
                                 else tr("Voir l'offre")), o["url"])

            # Rappel compact, une seule fois, apres la 3e offre.
            if i == 2 and len(offres) > 3:
                st.info("🤝 " + tr("Une offre t'intéresse ? On s'occupe du dossier, "
                                   "du visa et des traductions — voir nos services "
                                   "en bas de page."))

        # ---- Navigation ----------------------------------------------------
        if pages > 1:
            g, m, d = st.columns([1, 2, 1])
            with g:
                if st.button("‹ " + tr("Précédent"), key=f"prec_{type_p}",
                             disabled=page <= 1, use_container_width=True):
                    st.session_state[page_cle] = page - 1
                    st.rerun()
            with m:
                st.caption(f"<div style='text-align:center'>{page} / {pages}</div>",
                           unsafe_allow_html=True)
            with d:
                if st.button(tr("Suivant") + " ›", key=f"suiv_{type_p}",
                             disabled=fin >= total, use_container_width=True):
                    st.session_state[page_cle] = page + 1
                    st.rerun()

    return total_affiche
# ---------------------------------------------------------------------------
'''


def main() -> None:
    if not P.exists():
        print("jobs_api.py introuvable")
        sys.exit(1)
    src = P.read_text(encoding="utf-8")

    if "def chercher_page" in src:
        print("= jobs_api.py : deja patche")
        return

    m = re.search(r"^def afficher\(", src, re.M)
    if not m:
        print("? jobs_api.py : def afficher( introuvable — rien ecrit")
        sys.exit(2)

    # Fin de la fonction : la ligne `    return total` la plus proche.
    fin = re.search(r"^    return total\s*$", src[m.start():], re.M)
    if not fin:
        print("? jobs_api.py : `return total` de fin introuvable — rien ecrit")
        sys.exit(2)
    debut_abs = m.start()
    fin_abs = m.start() + fin.end()

    if DRY:
        n_lignes = src[debut_abs:fin_abs].count("\n")
        print(f"~ jobs_api.py : remplace afficher() ({n_lignes} lignes) "
              f"par la version paginee + CTA [DRY-RUN]")
        return

    bak = P.with_suffix(f".py.bak-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(P, bak)
    nouveau = src[:debut_abs] + NOUVEAU.lstrip("\n") + src[fin_abs:]

    try:
        ast.parse(nouveau)
    except SyntaxError as e:
        print(f"x syntaxe cassee ligne {e.lineno} — rien ecrit")
        sys.exit(1)

    P.write_text(nouveau, encoding="utf-8")
    print(f"v jobs_api.py : afficher() paginee + CTA, syntaxe OK ({bak.name})")
    print("\nVide le cache (nouvelles cles de page) :")
    print("  python -c \"import sqlite3;c=sqlite3.connect('data/mobilite.db',"
          "timeout=30);c.execute('DELETE FROM jobs_cache');c.commit();"
          "print('cache vide')\"")
    print("\nOptionnel — ajoute ces cles dans app/api/i18n.py pour l'anglais :")
    for cle in ("Offres", "sur environ", "page", "Précédent", "Suivant",
                "Postuler avec notre accompagnement"):
        print(f'   "{cle}"')


if __name__ == "__main__":
    main()
