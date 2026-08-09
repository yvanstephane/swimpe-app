#!/usr/bin/env python3
"""
patch_yorbity.py — Branche le registre de sources, corrige la reference et
la traduction des offres, renomme la carte Canada.

Ce qu'il fait, dans l'ordre :
  1. seed_mondial.py : "Emploi etudiant au Canada" -> "Emplois ouverts aux
     candidats internationaux". Le titre actuel promet ce que Job Bank ne peut
     pas donner : la sonde a montre fsrc=21 (Summer Jobs) + fglo=1 -> 0 offre.
  2. data/mobilite.db : meme renommage sur les lignes deja seedees, pour ne pas
     avoir a re-seeder (et creer des doublons).
  3. jobs_api.py : la reference affichee devient celle de l'EMPLOYEUR
     (o["reference"]) et non l'id interne tronque JOB-{id[:10]}, qui ne veut
     rien dire pour un recruteur.
  4. jobs_api.py : titre / lieu / extrait passent par traduction_offres quand
     tr() ne connait pas le texte (les offres sont dynamiques, tr() est un
     dictionnaire de cles statiques -> l'anglais ressortait tel quel).
  5. offres_sync.py : ajoute ingerer_sources(), qui boucle sur le registre
     au lieu de connaitre Job Bank en dur.

Idempotent : relancable sans degat. Sauvegarde .bak-<horodatage> avant chaque
modification. Verifie la syntaxe apres. Restaure si la syntaxe casse.

Usage :
    python scripts/patch_yorbity.py           # applique
    python scripts/patch_yorbity.py --dry     # montre sans ecrire
"""

from __future__ import annotations

import ast
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DRY = "--dry" in sys.argv
HORO = datetime.now().strftime("%Y%m%d-%H%M%S")

ANCIEN_TITRE = "Emploi étudiant au Canada — Job Bank gouvernement"
NOUVEAU_TITRE = "Emplois ouverts aux candidats internationaux — Job Bank"

resultats: list[str] = []


# --------------------------------------------------------------------------- #
def lire(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def ecrire(p: Path, contenu: str, n_patchs: int) -> bool:
    """Sauvegarde, ecrit, verifie la syntaxe. Restaure si ca casse."""
    if DRY:
        resultats.append(f"~ {p.name} : {n_patchs} patch(s) [DRY-RUN, rien ecrit]")
        return True

    bak = p.with_suffix(p.suffix + f".bak-{HORO}")
    shutil.copy2(p, bak)
    p.write_text(contenu, encoding="utf-8")

    if p.suffix == ".py":
        try:
            ast.parse(contenu)
        except SyntaxError as e:
            shutil.copy2(bak, p)
            resultats.append(f"x {p.name} : SYNTAXE CASSEE ligne {e.lineno} — restaure")
            return False

    resultats.append(f"v {p.name} : {n_patchs} patch(s), syntaxe OK ({bak.name})")
    return True


# --------------------------------------------------------------------------- #
# 1. seed_mondial.py — renommer la carte
# --------------------------------------------------------------------------- #
def patch_seed() -> None:
    p = RACINE / "scripts" / "seed_mondial.py"
    if not p.exists():
        resultats.append("- seed_mondial.py introuvable")
        return
    src = lire(p)
    if NOUVEAU_TITRE in src:
        resultats.append("= seed_mondial.py : deja renomme")
        return
    if ANCIEN_TITRE not in src:
        resultats.append("? seed_mondial.py : titre attendu absent, rien fait")
        return
    ecrire(p, src.replace(ANCIEN_TITRE, NOUVEAU_TITRE), 1)


# --------------------------------------------------------------------------- #
# 2. base — renommer les lignes deja seedees
# --------------------------------------------------------------------------- #
def patch_base() -> None:
    db = RACINE / "data" / "mobilite.db"
    if not db.exists():
        resultats.append("- data/mobilite.db introuvable")
        return
    if DRY:
        resultats.append("~ mobilite.db : UPDATE titre [DRY-RUN]")
        return
    con = sqlite3.connect(db)
    cur = con.execute(
        "UPDATE opportunites SET titre=? WHERE titre=?", (NOUVEAU_TITRE, ANCIEN_TITRE)
    )
    con.commit()
    n = cur.rowcount
    con.close()
    resultats.append(f"v mobilite.db : {n} ligne(s) renommee(s)")


# --------------------------------------------------------------------------- #
# 3+4. jobs_api.py — reference reelle + traduction des offres
# --------------------------------------------------------------------------- #
BLOC_TOFF = '''

# --- ajoute par patch_yorbity.py -------------------------------------------
def _langue_courante():
    """La cle i18n varie selon les pages ; on essaie les noms connus."""
    for cle in ("langue", "lang", "language"):
        v = st.session_state.get(cle)
        if v:
            return str(v)[:2].lower()
    return "fr"


def _toff(texte):
    """
    tr() est un dictionnaire de cles STATIQUES : un titre d'offre anglais
    n'y figure pas et ressortait tel quel. On tente d'abord tr(), puis
    traduction_offres (Ollama + cache SQLite).
    """
    if not texte:
        return texte
    try:
        traduit = tr(texte)
        if traduit and traduit != texte:
            return traduit
    except Exception:
        pass
    try:
        import traduction_offres
        return traduction_offres.traduire(texte, _langue_courante(), langue_source="en")
    except Exception:
        return texte
# ---------------------------------------------------------------------------
'''

REMPLACEMENTS_JOBS_API = [
    # reference : id interne tronque -> reference employeur
    (
        '''st.caption("📌 " + tr("Référence à indiquer dans le formulaire :")
                           + f" JOB-{o['id'][:10]}")''',
        '''st.caption("📌 " + tr("Référence à indiquer dans le formulaire :")
                           + " " + (o.get("reference") or f"JOB-{o['id'][:10]}"))''',
    ),
    # traduction des champs dynamiques
    ('entete = tr(o["titre"]) if o["titre"] else tr("Offre")',
     'entete = _toff(o["titre"]) if o["titre"] else tr("Offre")'),
    ('st.markdown("📍 " + tr(o["lieu"]))',
     'st.markdown("📍 " + _toff(o["lieu"]))'),
    ('st.write(tr(o["extrait"]) + "…")',
     'st.write(_toff(o["extrait"]) + "…")'),
]


def patch_jobs_api() -> None:
    p = RACINE / "app" / "api" / "jobs_api.py"
    if not p.exists():
        resultats.append("- jobs_api.py introuvable")
        return
    src = lire(p)
    n = 0

    if "_toff" not in src:
        # insere le bloc juste apres les imports (apres la ligne MAX_OFFRES)
        ancre = "MAX_OFFRES = 8"
        if ancre in src:
            src = src.replace(ancre, ancre + BLOC_TOFF, 1)
            n += 1
        else:
            resultats.append("? jobs_api.py : ancre MAX_OFFRES absente, _toff non injecte")

    for avant, apres in REMPLACEMENTS_JOBS_API:
        if apres in src:
            continue
        if avant in src:
            src = src.replace(avant, apres, 1)
            n += 1

    if n == 0:
        resultats.append("= jobs_api.py : deja patche")
        return
    ecrire(p, src, n)


# --------------------------------------------------------------------------- #
# 5. offres_sync.py — ingestion via le registre
# --------------------------------------------------------------------------- #
BLOC_INGERER = '''

# --- ajoute par patch_yorbity.py -------------------------------------------
def ingerer_sources(dest_code, sans_permis=None):
    """
    Ingere via le REGISTRE de sources (app/api/sources/) plutot que via une
    source codee en dur. Ajouter un pays = ecrire un adaptateur, rien d'autre.

    sans_permis=True  -> ne garde que les offres postulables SANS permis de
                         travail. Au Canada, aucun emploi etudiant ne l'est :
                         le travail hors campus exige un permis d'etudes valide.
    Retourne (ajoutees, ignorees).
    """
    try:
        from sources import registre
    except Exception as e:
        print("registre indisponible :", e)
        return 0, 0

    ajout, deja = 0, 0
    con = sqlite3.connect(DB)
    for type_p in ("stage", "emploi", "metier"):
        for o in registre.collecter(dest_code, type_p, sans_permis=sans_permis):
            if _existe(con, o.get("url", ""), o.get("titre", ""), dest_code.upper()):
                deja += 1
                continue
            con.execute(
                "INSERT INTO opportunites(type,titre,destination,origines_eligibles,"
                "niveau,domaine,montant,deadline,source_url,maj,statut) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (type_p, o.get("titre", ""), dest_code.upper(), "TOUS", "",
                 o.get("entreprise", ""), o.get("salaire", ""), "",
                 o.get("url", ""), datetime.date.today().isoformat(), "auto"))
            ajout += 1
    con.commit()
    con.close()
    return ajout, deja


def prechauffer_traductions(offres, langues=None):
    """Traduit d'avance les offres : l'utilisateur n'attend jamais Ollama."""
    try:
        import traduction_offres
        traduction_offres.prechauffer(offres, langues)
    except Exception as e:
        print("prechauffage impossible :", e)
# ---------------------------------------------------------------------------
'''


def patch_offres_sync() -> None:
    p = RACINE / "app" / "api" / "offres_sync.py"
    if not p.exists():
        resultats.append("- offres_sync.py introuvable")
        return
    src = lire(p)
    if "def ingerer_sources" in src:
        resultats.append("= offres_sync.py : deja patche")
        return
    ancre = "def verifier_liens("
    if ancre not in src:
        resultats.append("? offres_sync.py : ancre verifier_liens absente")
        return
    src = src.replace(ancre, BLOC_INGERER.lstrip("\n") + "\n" + ancre, 1)
    ecrire(p, src, 1)


# --------------------------------------------------------------------------- #
def main() -> None:
    if DRY:
        print(">>> DRY-RUN : rien ne sera ecrit\n")
    patch_seed()
    patch_base()
    patch_jobs_api()
    patch_offres_sync()

    print()
    for r in resultats:
        print(" ", r)
    print()
    if any(r.startswith("x") for r in resultats):
        print("ECHEC : au moins un fichier a ete restaure. Rien n'est casse.")
        sys.exit(1)
    print("FINI — relance : yorbity")
    print("Retour arriere : mv <fichier>.bak-%s <fichier>" % HORO)


if __name__ == "__main__":
    main()
