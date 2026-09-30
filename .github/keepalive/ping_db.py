#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ping_db.py - Keep-alive Supabase pour Swimpe.
Ecrit un battement REEL en base (INSERT/UPDATE d'un timestamp), ce qui compte
comme activite pour Supabase et empeche la mise en pause du plan gratuit
(~7 jours d'inactivite). Lance automatiquement par GitHub Actions.
Une simple connexion ne suffit PAS : il faut une ecriture reelle.
"""
import os
import sys


def main():
    dsn = os.environ.get("DATABASE_URL", "").strip()
    if not dsn:
        print("ERREUR : secret DATABASE_URL absent.")
        return 1
    try:
        import psycopg2
    except ImportError:
        print("ERREUR : psycopg2 non installe.")
        return 1
    try:
        con = psycopg2.connect(dsn, connect_timeout=15)
    except Exception as e:
        print("ERREUR de connexion :", e)
        return 1
    try:
        con.autocommit = True
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS heartbeat ("
            "id INT PRIMARY KEY, "
            "last_ping TIMESTAMPTZ NOT NULL, "
            "count BIGINT NOT NULL DEFAULT 0)"
        )
        cur.execute(
            "INSERT INTO heartbeat (id, last_ping, count) VALUES (1, now(), 1) "
            "ON CONFLICT (id) DO UPDATE SET "
            "last_ping = EXCLUDED.last_ping, count = heartbeat.count + 1"
        )
        cur.execute("SELECT last_ping, count FROM heartbeat WHERE id = 1")
        row = cur.fetchone()
        print("Battement OK -> last_ping=%s, count=%s" % (row[0], row[1]))
        cur.close()
        return 0
    except Exception as e:
        print("ERREUR SQL :", e)
        return 1
    finally:
        try:
            con.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
