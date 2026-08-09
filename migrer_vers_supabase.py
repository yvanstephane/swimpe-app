#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Migration SQLite -> PostgreSQL/Supabase pour Swimpe."""
import sqlite3, os, sys

SQLITE_DB = "data/mobilite.db"
for cand in (SQLITE_DB, "mobilite.db", os.path.expanduser("~/mobilite-ia/data/mobilite.db")):
    if os.path.exists(cand):
        SQLITE_DB = cand
        break

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if not DATABASE_URL:
    print("ERREUR: DATABASE_URL manquant. Faites d'abord: export DATABASE_URL=\"postgresql://...\"")
    sys.exit(1)

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    print("ERREUR: psycopg2 manquant. Faites: pip install psycopg2-binary")
    sys.exit(1)

def type_pg(sqlite_type, est_pk_autoincr):
    if est_pk_autoincr:
        return "SERIAL PRIMARY KEY"
    t = (sqlite_type or "TEXT").upper()
    if "INT" in t: return "BIGINT"
    if "REAL" in t or "FLOA" in t or "DOUB" in t: return "DOUBLE PRECISION"
    if "BLOB" in t: return "BYTEA"
    return "TEXT"

def main():
    print("Source SQLite :", SQLITE_DB)
    print("Cible Postgres:", DATABASE_URL.split('@')[-1][:40], "...\n")
    sconn = sqlite3.connect(SQLITE_DB); sconn.row_factory = sqlite3.Row
    scur = sconn.cursor()
    pconn = psycopg2.connect(DATABASE_URL); pcur = pconn.cursor()
    tables = [r[0] for r in scur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    total = 0
    for t in tables:
        cols = scur.execute("PRAGMA table_info('%s')" % t).fetchall()
        ddl = scur.execute("SELECT sql FROM sqlite_master WHERE name=?", (t,)).fetchone()[0]
        autoincr = "AUTOINCREMENT" in ddl.upper()
        pk_cols = [c["name"] for c in cols if c["pk"]]
        composite = len(pk_cols) > 1
        defs = []; colnames = []
        for c in cols:
            colnames.append(c["name"])
            est_pk_ai = (bool(c["pk"]) and autoincr and not composite and "INT" in (c["type"] or "").upper())
            coltype = type_pg(c["type"], est_pk_ai)
            if c["pk"] and not est_pk_ai and not composite and "PRIMARY KEY" not in coltype:
                coltype += " PRIMARY KEY"
            defs.append('"%s" %s' % (c["name"], coltype))
        if composite:
            defs.append('PRIMARY KEY (%s)' % ", ".join('"%s"' % c for c in pk_cols))
        pcur.execute('DROP TABLE IF EXISTS "%s" CASCADE' % t)
        pcur.execute('CREATE TABLE "%s" (%s)' % (t, ", ".join(defs)))
        rows = scur.execute("SELECT * FROM '%s'" % t).fetchall()
        if rows:
            cols_q = ", ".join('"%s"' % c for c in colnames)
            valeurs = [tuple(r[c] for c in colnames) for r in rows]
            execute_values(pcur, 'INSERT INTO "%s" (%s) VALUES %%s' % (t, cols_q), valeurs)
            if autoincr and "id" in colnames:
                pcur.execute("SELECT setval(pg_get_serial_sequence('\"%s\"','id'), COALESCE((SELECT MAX(id) FROM \"%s\"),1))" % (t, t))
        total += len(rows)
        print("  OK %-26s %6d lignes" % (t, len(rows)))
    pconn.commit(); pcur.close(); pconn.close(); sconn.close()
    print("\nMigration terminee : %d tables, %d lignes transferees." % (len(tables), total))

if __name__ == "__main__":
    main()
