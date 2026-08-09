#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""file_plans.py — File d'attente des demandes de plan personnalise (Swimpe)"""
import sqlite3
try:
    import sqlite3 as _sqlite3
    from importlib import import_module as _imp
    _dbc = _imp("db")
    if getattr(_dbc, "MODE_PG", False):
        _sqlite3.connect = lambda *a, **k: _dbc.connect(*a, **k)
        _sqlite3.Row = _dbc.Row
except Exception:
    pass
import datetime

DB = "data/mobilite.db"

def init():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS demandes_plan(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, origine TEXT, destination TEXT, offre TEXT,
        statut TEXT DEFAULT 'en_attente', resultat TEXT, erreur TEXT,
        cree_le TEXT, traite_le TEXT)""")
    con.commit(); con.close()

def creer_demande(user_id, origine, destination, offre=""):
    init()
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    exist = con.execute(
        "SELECT id FROM demandes_plan WHERE user_id=? AND origine=? "
        "AND destination=? AND statut IN ('en_attente','en_cours') "
        "ORDER BY id DESC LIMIT 1", (user_id, origine, destination)).fetchone()
    if exist:
        con.close(); return exist["id"]
    cur = con.execute(
        "INSERT INTO demandes_plan(user_id,origine,destination,offre,statut,cree_le) "
        "VALUES(?,?,?,?, 'en_attente', ?)",
        (user_id, origine, destination, offre,
         datetime.datetime.now().isoformat(timespec="seconds")))
    con.commit(); rid = cur.lastrowid; con.close(); return rid

def mes_demandes(user_id):
    init()
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    rows = con.execute("SELECT * FROM demandes_plan WHERE user_id=? ORDER BY id DESC",
                       (user_id,)).fetchall()
    con.close(); return [dict(r) for r in rows]

def demande(rid):
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    r = con.execute("SELECT * FROM demandes_plan WHERE id=?", (rid,)).fetchone()
    con.close(); return dict(r) if r else None

def prochaine_a_traiter():
    init()
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    r = con.execute("SELECT * FROM demandes_plan WHERE statut='en_attente' "
                    "ORDER BY id ASC LIMIT 1").fetchone()
    if not r:
        con.close(); return None
    con.execute("UPDATE demandes_plan SET statut='en_cours' WHERE id=?", (r["id"],))
    con.commit(); con.close(); return dict(r)

def livrer_resultat(rid, plan_md):
    con = sqlite3.connect(DB)
    con.execute("UPDATE demandes_plan SET statut='pret', resultat=?, traite_le=? WHERE id=?",
                (plan_md, datetime.datetime.now().isoformat(timespec="seconds"), rid))
    con.commit(); con.close()

def marquer_erreur(rid, message):
    con = sqlite3.connect(DB)
    con.execute("UPDATE demandes_plan SET statut='en_attente', erreur=? WHERE id=?",
                (str(message)[:500], rid))
    con.commit(); con.close()

def stats():
    init()
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    rows = con.execute("SELECT statut, COUNT(*) n FROM demandes_plan GROUP BY statut").fetchall()
    con.close(); return {r["statut"]: r["n"] for r in rows}
