#!/usr/bin/env python3
"""
nettoyer_offres.py (v2) — Repare la table `opportunites`.

Ce que le premier passage a revele :

  * dedup : 97 -> 57. Quarante doublons, crees par seed_mondial.py relance
    plusieurs fois (il insere sans verifier l'existant).

  * La carte Job Bank restait en DOUBLE (rowid 50 et 96) : mon groupement
    incluait source_url, et ces deux lignes portent des URL differentes
    (l'ancienne "https://www.jobbank.gc.ca" et la nouvelle "?fglo=1").
    -> --dedup-carte regroupe sur (titre, destination, type) seulement.

  * 76 offres ingerees au lieu de ~13 : ingerer_sources() appelle collecter()
    SANS mot-cle, donc ramasse tout le flux fglo=1 (camionneurs, medecins...).
    Pire : la table `opportunites` n'a ni colonne `description` ni `reference`.
    Les offres y perdent leur description -- or c'est precisement ce qu'on
    voulait afficher. Ces 76 lignes (statut='auto') sont a purger.
    Le bon circuit est jobs_api.ecran(), qui a deja expander + description
    + salaire + reference + lien + toggles admin.

  * seed_mondial.py recreera les doublons a chaque lancement.
    -> --index pose un index UNIQUE qui rend l'operation impossible.

Usage :
    python scripts/nettoyer_offres.py                # diagnostic seul
    python scripts/nettoyer_offres.py --purger-auto  # retire les 76 offres
    python scripts/nettoyer_offres.py --dedup        # doublons stricts
    python scripts/nettoyer_offres.py --dedup-carte  # doublons hors URL
    python scripts/nettoyer_offres.py --texte        # corps de carte
    python scripts/nettoyer_offres.py --index        # empeche les futurs doublons
    python scripts/nettoyer_offres.py --reparer      # tout sauf --index

Sauvegarde la base avant toute ecriture.
"""

from __future__ import annotations

import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DB = RACINE / "data" / "mobilite.db"

TITRE = "Emplois ouverts aux candidats internationaux — Job Bank"
BON_LIEN = "https://www.jobbank.gc.ca/jobsearch/jobsearch?fglo=1&sort=M"

NOUVEAU_CORPS = (
    "Employeurs canadiens qui recrutent hors du Canada. Un permis de travail "
    "est requis : ces offres en sont la porte d'entree. Attention, ce ne sont "
    "pas des emplois etudiants — le travail hors campus (20 h/semaine) exige "
    "d'avoir deja un permis d'etudes valide."
)


def sauver() -> None:
    bak = DB.with_suffix(f".db.bak-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(DB, bak)
    print(f"  sauvegarde : {bak.name}")


def compte(con) -> int:
    return con.execute("SELECT COUNT(*) FROM opportunites").fetchone()[0]


# --------------------------------------------------------------------------- #
def diagnostic(con) -> None:
    print("\n--- Doublons stricts (titre + destination + type + source_url)")
    rows = con.execute(
        "SELECT titre, destination, COUNT(*) n FROM opportunites "
        "GROUP BY titre, destination, type, COALESCE(source_url,'') "
        "HAVING n > 1 ORDER BY n DESC LIMIT 8"
    ).fetchall()
    print("  aucun" if not rows else "")
    for t, d, n in rows:
        print(f"  {n}x  [{d}] {t[:58]}")

    print("\n--- Doublons de carte (meme titre + destination + type, URL differente)")
    rows = con.execute(
        "SELECT titre, destination, COUNT(*) n FROM opportunites "
        "GROUP BY titre, destination, type HAVING n > 1 ORDER BY n DESC LIMIT 8"
    ).fetchall()
    print("  aucun" if not rows else "")
    for t, d, n in rows:
        print(f"  {n}x  [{d}] {t[:58]}")

    print("\n--- Carte Job Bank")
    for r in con.execute(
        "SELECT rowid, type, source_url, substr(COALESCE(montant,''),1,55) "
        "FROM opportunites WHERE titre = ?", (TITRE,)
    ):
        print(f"  rowid={r[0]} type={r[1]}")
        print(f"    url  = {r[2]}")
        print(f"    corps= {r[3]!r}")

    print("\n--- Par statut")
    for s, n in con.execute("SELECT statut, COUNT(*) FROM opportunites GROUP BY statut"):
        note = "  <- ingestion Job Bank, sans description : a purger" if s == "auto" else ""
        print(f"  {s!r}: {n}{note}")

    print(f"\n  total : {compte(con)} opportunites")


# --------------------------------------------------------------------------- #
def purger_auto(con) -> None:
    """
    Les offres statut='auto' viennent d'ingerer_sources(). Elles n'ont ni
    description ni reference (colonnes absentes) : inutilisables a l'affichage.
    Job Bank doit passer par jobs_api.ecran(), pas par la table opportunites.
    """
    n = con.execute("SELECT COUNT(*) FROM opportunites WHERE statut='auto'").fetchone()[0]
    con.execute("DELETE FROM opportunites WHERE statut='auto'")
    con.commit()
    print(f"  purge auto : {n} ligne(s) supprimee(s)")


def dedup(con) -> None:
    avant = compte(con)
    con.execute(
        "DELETE FROM opportunites WHERE rowid NOT IN ("
        " SELECT MIN(rowid) FROM opportunites"
        " GROUP BY titre, destination, type, COALESCE(source_url,''))"
    )
    con.commit()
    print(f"  dedup strict : {avant} -> {compte(con)}")


def dedup_carte(con) -> None:
    """Ignore source_url : garde la ligne au bon lien, sinon la plus ancienne."""
    avant = compte(con)
    con.execute("UPDATE opportunites SET source_url=? WHERE titre=?", (BON_LIEN, TITRE))
    con.execute(
        "DELETE FROM opportunites WHERE rowid NOT IN ("
        " SELECT MIN(rowid) FROM opportunites GROUP BY titre, destination, type)"
    )
    con.commit()
    print(f"  dedup carte : {avant} -> {compte(con)}")


def corriger_texte(con) -> None:
    cur = con.execute(
        "UPDATE opportunites SET montant=? WHERE titre=?", (NOUVEAU_CORPS, TITRE)
    )
    con.commit()
    print(f"  texte : {cur.rowcount} carte(s) corrigee(s)")


def poser_index(con) -> None:
    """Rend les doublons impossibles. seed_mondial devra utiliser INSERT OR IGNORE."""
    try:
        con.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_opp_unique "
            "ON opportunites(titre, destination, type)"
        )
        con.commit()
        print("  index UNIQUE(titre, destination, type) pose")
        print("    -> dans seed_mondial.py, remplace INSERT INTO par INSERT OR IGNORE INTO")
    except sqlite3.IntegrityError as e:
        print(f"  index impossible, doublons restants : {e}")
        print("    lance d'abord --dedup-carte")


# --------------------------------------------------------------------------- #
def main() -> None:
    if not DB.exists():
        print(f"Base introuvable : {DB}")
        sys.exit(1)

    args = set(sys.argv[1:])
    con = sqlite3.connect(DB)
    diagnostic(con)

    if not args:
        print("\nRien fait. Options : --purger-auto --dedup --dedup-carte "
              "--texte --index --reparer")
        return

    reparer = "--reparer" in args
    print()
    sauver()

    if reparer or "--purger-auto" in args:
        purger_auto(con)
    if reparer or "--dedup" in args:
        dedup(con)
    if reparer or "--dedup-carte" in args:
        dedup_carte(con)
    if reparer or "--texte" in args:
        corriger_texte(con)
    if "--index" in args:
        poser_index(con)

    print("\n--- Apres")
    diagnostic(con)
    con.close()
    print("\nRelance : yorbity")


if __name__ == "__main__":
    main()
