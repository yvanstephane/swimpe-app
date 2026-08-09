#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inspecteur_fiches.py — Yorbity (READ-ONLY, ne modifie rien)
===========================================================
But : localiser OÙ vit le contenu des fiches pays (résumés, étapes)
      pour caler le critère des étoiles ⭐.

Usage :
    cd ~/mobilite-ia && source .venv/bin/activate
    python inspecteur_fiches.py

Puis : copier TOUTE la sortie dans Claude.
"""
import sqlite3, os, glob, re, sys, datetime

SEP = "=" * 64
DB_HINT = "data/mobilite.db"   # vu dans ta sortie précédente
MODULES = ["pays_i18n.py", "destinations_monde.py", "pays_monde.py",
           "config_projets.py", "config_projets.py", "traduction.py"]
PROJETS = ["etudes", "travail", "tourisme", "affaires", "immigration"]


def find_db():
    for c in (os.environ.get("YORBITY_DB"), DB_HINT, "mobilite.db"):
        if c and os.path.exists(c):
            return c
    for f in glob.glob("**/*.db", recursive=True):
        if ".venv" not in f and "site-packages" not in f:
            return f
    sys.exit("❌ base introuvable")


def dump_table(con, table, limit=None):
    cur = con.execute(f"SELECT * FROM {table}" + (f" LIMIT {limit}" if limit else ""))
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print(f"\n  ── {table}  ({len(rows)}{'+' if limit and len(rows)==limit else ''} lignes) "
          f"colonnes: {', '.join(cols)}")
    for r in rows:
        cells = []
        for v in r:
            s = "" if v is None else str(v).replace("\n", "⏎")
            cells.append(s[:45] + ("…" if len(s) > 45 else ""))
        print("     " + " | ".join(cells))


def main():
    db = find_db()
    con = sqlite3.connect(db)
    print(SEP)
    print(f"INSPECTEUR FICHES — {datetime.datetime.now():%Y-%m-%d %H:%M}")
    print(f"Base : {os.path.abspath(db)}")
    print(SEP)

    # [1] toutes les tables + rowcount + colonnes
    print("\n[1] TOUTES LES TABLES")
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    for t in tables:
        cols = [c[1] + ":" + (c[2] or "?") for c in con.execute(f"PRAGMA table_info({t})")]
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:22s} {n:5d} lignes | {', '.join(cols)}")

    # [2] dumps complets des petites tables de config
    print("\n[2] DUMPS DE CONFIG")
    for t in ("config_pays", "config_origines", "config_services", "config_tarifs"):
        if t in tables:
            dump_table(con, t, limit=8 if t == "config_pays" else None)

    # [3] trad_cache : structure + échantillon
    if "trad_cache" in tables:
        print("\n[3] trad_cache (échantillon)")
        dump_table(con, "trad_cache", limit=6)

    # [4] recherche de contenu long dans TOUTES les colonnes texte
    print("\n[4] COLONNES CONTENANT DU TEXTE LONG (>60 car.) — piste 'fiches en base'")
    trouve = False
    for t in tables:
        cols = [c[1] for c in con.execute(f"PRAGMA table_info({t})")]
        for c in cols:
            try:
                mx = con.execute(
                    f"SELECT MAX(LENGTH(CAST({c} AS TEXT))) FROM {t}").fetchone()[0] or 0
            except sqlite3.Error:
                continue
            if mx and mx > 60:
                ex = con.execute(
                    f"SELECT {c} FROM {t} WHERE LENGTH(CAST({c} AS TEXT))>60 LIMIT 1"
                ).fetchone()[0]
                ex = str(ex).replace("\n", "⏎")[:70]
                print(f"  {t}.{c:20s} maxlen={mx:5d}  ex: {ex}…")
                trouve = True
    if not trouve:
        print("  (aucune) → les fiches ne sont PAS dans la base : elles sont dans les .py")

    con.close()

    # [5] introspection des modules Python
    print("\n[5] MODULES PYTHON — recherche du contenu des fiches")
    kw_fiche = re.compile(r"(resum|résum|etape|étape|fiche|démarche|demarche|desc)", re.I)
    for m in dict.fromkeys(MODULES):          # dédoublonne
        if not os.path.exists(m):
            print(f"\n  ── {m} : absent")
            continue
        src = open(m, encoding="utf-8", errors="replace").read()
        lignes = src.splitlines()
        print(f"\n  ── {m}  ({len(lignes)} lignes)")
        # top-level dict/list assignments
        defs = re.findall(r"^([A-Za-z_][\w]*)\s*=\s*[\[{]", src, re.M)
        if defs:
            print(f"     structures top-level : {', '.join(dict.fromkeys(defs))}")
        # fonctions
        fns = re.findall(r"^def\s+([a-zA-Z_]\w*)", src, re.M)
        if fns:
            print(f"     fonctions : {', '.join(fns[:15])}{'…' if len(fns)>15 else ''}")
        # lignes contenant un mot-clé de fiche (max 6)
        hits = [(i + 1, l.strip()) for i, l in enumerate(lignes) if kw_fiche.search(l)]
        if hits:
            print(f"     lignes 'fiche' ({len(hits)}) — échantillon :")
            for ln, txt in hits[:6]:
                print(f"        L{ln}: {txt[:80]}")
        # présence des codes/noms de projet
        pj = [p for p in PROJETS if re.search(rf"\b{p}\b", src)]
        if pj:
            print(f"     projets cités : {', '.join(pj)}")
        # présence de 'FR' comme clé (indice de dict pays)
        if re.search(r"""['"]FR['"]\s*:""", src):
            print("     → contient des clés pays type 'FR': ... (dict de fiches probable)")

    print("\n" + SEP)
    print("FIN — copie TOUTE cette sortie dans Claude")
    print(SEP)


if __name__ == "__main__":
    main()
