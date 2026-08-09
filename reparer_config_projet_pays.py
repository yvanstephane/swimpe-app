#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reparer_config_projet_pays.py — Yorbity
=======================================
Corrige la table config_projet_pays créée par erreur avec un mauvais schéma.
Le BON schéma est celui de app/api/config_projets.py :
    config_projet_pays(projet, role, pays, etoile, actif, force_admin)

Ce script :
  1. sauvegarde la base (copie .bak horodatée)
  2. inspecte le schéma actuel de config_projet_pays
  3. si les colonnes ne correspondent pas → DROP + recréation propre (vide)
  4. vérifie que les requêtes de l'app passent désormais

Il NE seed PAS les étoiles : c'est l'app qui le fait (admin_projets._seed_initial)
avec les vraies données D/ORIGINES.

Usage :
    cd ~/mobilite-ia && python reparer_config_projet_pays.py
    python reparer_config_projet_pays.py --dry-run   # montre, n'écrit rien
"""
import sqlite3, os, sys, shutil, glob, datetime

DRY = "--dry-run" in sys.argv
SEP = "=" * 64

# schéma cible (exactement celui de config_projets.py._init)
COLS_CIBLE = {"projet", "role", "pays", "etoile", "actif", "force_admin"}
DDL_CIBLE = """CREATE TABLE config_projet_pays(
    projet TEXT, role TEXT, pays TEXT,
    etoile INT DEFAULT 0, actif INT DEFAULT 0,
    force_admin INT DEFAULT 0,
    PRIMARY KEY(projet, role, pays))"""


def find_db():
    for c in (os.environ.get("YORBITY_DB"), "data/mobilite.db", "mobilite.db"):
        if c and os.path.exists(c):
            return c
    for f in glob.glob("**/*.db", recursive=True):
        if ".venv" not in f and "site-packages" not in f:
            return f
    sys.exit("❌ base introuvable (lance depuis ~/mobilite-ia)")


def colonnes(con):
    return {c[1] for c in con.execute("PRAGMA table_info(config_projet_pays)")}


def existe(con):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                       "AND name='config_projet_pays'").fetchone() is not None


def main():
    db = find_db()
    print(SEP)
    print(f"RÉPARATION config_projet_pays — {datetime.datetime.now():%Y-%m-%d %H:%M}")
    print(f"Base : {os.path.abspath(db)}" + ("   [DRY-RUN]" if DRY else ""))
    print(SEP)

    con = sqlite3.connect(db)

    if not existe(con):
        print("\nTable absente → création propre.")
        if not DRY:
            con.execute(DDL_CIBLE)
            con.commit()
        etat = "créée"
    else:
        cols = colonnes(con)
        nb = con.execute("SELECT COUNT(*) FROM config_projet_pays").fetchone()[0]
        print(f"\nSchéma actuel : {', '.join(sorted(cols))}  ({nb} lignes)")
        if cols == COLS_CIBLE:
            print("✓ Schéma déjà correct — rien à réparer.")
            etat = "déjà correct"
        else:
            manquantes = COLS_CIBLE - cols
            en_trop = cols - COLS_CIBLE
            print("✗ Schéma INCORRECT.")
            print(f"   colonnes manquantes : {', '.join(sorted(manquantes)) or '—'}")
            print(f"   colonnes en trop     : {', '.join(sorted(en_trop)) or '—'}")

            # sauvegarde AVANT toute modification
            bak = f"{db}.bak-{datetime.datetime.now():%Y%m%d-%H%M%S}"
            print(f"\n→ sauvegarde : {bak}")
            if not DRY:
                shutil.copy2(db, bak)

            print("→ suppression de la table cassée + recréation propre (vide).")
            if not DRY:
                con.execute("DROP TABLE config_projet_pays")
                con.execute(DDL_CIBLE)
                con.commit()
            etat = "réparée"

    # vérification : les requêtes exactes de l'app doivent passer
    print("\n[VÉRIF] requêtes de config_projets.py")
    ok = True
    try:
        con.execute("SELECT pays, etoile, actif FROM config_projet_pays "
                    "WHERE projet=? AND role=?", ("Formation (admission)", "destination")).fetchall()
        print("  ✓ SELECT pays, etoile, actif … OK")
    except sqlite3.Error as e:
        ok = False; print(f"  ✗ SELECT échoue : {e}")
    if not DRY:
        try:
            con.execute("INSERT OR REPLACE INTO config_projet_pays"
                        "(projet,role,pays,etoile,actif,force_admin) VALUES(?,?,?,1,1,0)",
                        ("__test__", "destination", "__test__"))
            con.execute("DELETE FROM config_projet_pays WHERE projet='__test__'")
            con.commit()
            print("  ✓ INSERT(projet,role,pays,…) OK")
        except sqlite3.Error as e:
            ok = False; print(f"  ✗ INSERT échoue : {e}")

    con.close()
    print("\n" + SEP)
    print(f"RÉSULTAT : table {etat}." + ("" if ok else "  ⚠️ vérif KO"))
    print("Prochaine étape : relance l'app, ouvre l'admin → « 🎛 Configuration par")
    print("projet » : le seed des étoiles se fait automatiquement à ce moment-là.")
    print(SEP)


if __name__ == "__main__":
    main()
