#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inspecteur2.py — Yorbity (READ-ONLY)
====================================
Cible : tables `destinations` et `opportunites` (contenu des fiches),
        pour caler le critère des étoiles ⭐ (projet × pays).

Usage :
    cd ~/mobilite-ia && python inspecteur2.py
Puis copier TOUTE la sortie dans Claude (elle est courte).
"""
import sqlite3, os, glob, sys, datetime

SEP = "=" * 64
DB_HINT = "data/mobilite.db"


def find_db():
    for c in (os.environ.get("YORBITY_DB"), DB_HINT, "mobilite.db"):
        if c and os.path.exists(c):
            return c
    for f in glob.glob("**/*.db", recursive=True):
        if ".venv" not in f and "site-packages" not in f:
            return f
    sys.exit("❌ base introuvable")


def pragma(con, t):
    return [(c[1], c[2] or "?") for c in con.execute(f"PRAGMA table_info({t})")]


def dump(con, t, n=10):
    if not con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone():
        print(f"\n  ── {t} : ABSENTE")
        return
    cols = pragma(con, t)
    total = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"\n  ── {t}  ({total} lignes)")
    print("     colonnes : " + ", ".join(f"{c}:{ty}" for c, ty in cols))
    names = [c for c, _ in cols]

    # colonnes candidates pays / projet / contenu
    def cand(motifs):
        return [n2 for n2 in names if any(m in n2.lower() for m in motifs)]
    c_pays = cand(("pays", "code", "iso", "destination", "pays_code"))
    c_proj = cand(("projet", "type", "categorie", "catégorie", "service", "motif"))
    c_ctn = cand(("fiche", "resume", "résum", "etape", "étape", "contenu", "desc", "texte"))
    print(f"     → candidats PAYS   : {c_pays or '—'}")
    print(f"     → candidats PROJET : {c_proj or '—'}")
    print(f"     → candidats CONTENU: {c_ctn or '—'}")

    # valeurs distinctes des colonnes projet/pays (si peu nombreuses)
    for c in (c_proj + c_pays):
        try:
            vals = [str(r[0]) for r in con.execute(
                f"SELECT DISTINCT {c} FROM {t} WHERE {c} IS NOT NULL LIMIT 40")]
            if 0 < len(vals) <= 40:
                print(f"     distinct {c} ({len(vals)}): {', '.join(vals[:40])}")
        except sqlite3.Error:
            pass

    # complétude : lignes avec au moins une colonne contenu non vide
    if c_ctn:
        cond = " OR ".join(f"LENGTH(TRIM(CAST({c} AS TEXT)))>20" for c in c_ctn)
        try:
            docn = con.execute(f"SELECT COUNT(*) FROM {t} WHERE {cond}").fetchone()[0]
            print(f"     lignes avec contenu (>20 car. sur {c_ctn}) : {docn}/{total}")
        except sqlite3.Error:
            pass

    # échantillon
    print(f"     échantillon ({min(n, total)} lignes) :")
    for r in con.execute(f"SELECT * FROM {t} LIMIT {n}"):
        cells = []
        for name, v in zip(names, r):
            s = "" if v is None else str(v).replace("\n", "⏎")
            cells.append(f"{name}={s[:38]}{'…' if len(s) > 38 else ''}")
        print("        " + " | ".join(cells))


def main():
    db = find_db()
    con = sqlite3.connect(db)
    print(SEP)
    print(f"INSPECTEUR 2 (destinations/opportunites) — {datetime.datetime.now():%H:%M}")
    print(f"Base : {os.path.abspath(db)}")
    print(SEP)

    print("\n[1] TOUTES LES TABLES")
    for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
        t = r[0]
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        cols = ", ".join(c[1] for c in con.execute(f"PRAGMA table_info({t})"))
        print(f"  {t:22s} {n:5d} | {cols}")

    print("\n[2] TABLES DE CONTENU")
    for t in ("destinations", "opportunites"):
        dump(con, t, n=10)

    # où sont les modules .py ? (résout le mystère 'absent')
    print("\n[3] LOCALISATION DES MODULES .py")
    here = glob.glob("*.py")
    sub = [f for f in glob.glob("**/*.py", recursive=True)
           if ".venv" not in f and "site-packages" not in f and "/" in f]
    print(f"  dans le dossier courant : {', '.join(sorted(here)) or '—'}")
    print(f"  dans des sous-dossiers  : {', '.join(sorted(sub)[:20]) or '—'}")

    con.close()
    print("\n" + SEP)
    print("FIN — copie TOUTE cette sortie dans Claude")
    print(SEP)


if __name__ == "__main__":
    main()
