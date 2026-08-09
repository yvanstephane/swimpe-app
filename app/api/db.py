#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
db.py — Couche de compatibilité base de données pour Swimpe
===========================================================
Permet au code écrit pour SQLite de fonctionner AUSSI sur PostgreSQL/Supabase,
SANS réécrire les 21 fichiers.

Principe : on remplace `sqlite3.connect(DB)` par `db.connect()`.
- En LOCAL (pas de DATABASE_URL) → SQLite pur, comportement identique à avant.
- En LIGNE (DATABASE_URL défini)  → PostgreSQL, avec traduction automatique
  de la syntaxe SQLite vers PostgreSQL à la volée.

Traductions automatiques appliquées aux requêtes :
  - placeholders  ?           → %s
  - INSERT OR REPLACE INTO    → INSERT ... ON CONFLICT DO UPDATE
  - INSERT OR IGNORE INTO     → INSERT ... ON CONFLICT DO NOTHING
  - PRAGMA ...                → ignoré (spécifique SQLite)
  - .lastrowid                → émulé via RETURNING id
  - row_factory = Row         → accès par nom de colonne émulé
"""
import os
import re

def _lire_secret(cle, defaut=""):
    v = os.environ.get(cle)
    if v:
        return v
    try:
        import streamlit as _st
        if hasattr(_st, "secrets") and cle in _st.secrets:
            return str(_st.secrets[cle])
    except Exception:
        pass
    return defaut

try:
    import streamlit as _st_init
    if hasattr(_st_init, "secrets"):
        for _k in list(_st_init.secrets.keys()):
            if _k not in os.environ:
                try:
                    os.environ[_k] = str(_st_init.secrets[_k])
                except Exception:
                    pass
except Exception:
    pass

DATABASE_URL = _lire_secret("DATABASE_URL", "").strip()
MODE_PG = bool(DATABASE_URL)   # True si on doit parler PostgreSQL


# ─────────────────────────────────────────────────────────────
# MODE LOCAL : SQLite pur (aucune traduction, comportement natif)
# ─────────────────────────────────────────────────────────────
if not MODE_PG:
    import sqlite3

    def connect(chemin="data/mobilite.db", **kw):
        kw.setdefault("timeout", 30)
        con = sqlite3.connect(chemin, **kw)
        try:
            con.execute("PRAGMA busy_timeout=30000")
        except Exception:
            pass
        return con

    Row = sqlite3.Row


# ─────────────────────────────────────────────────────────────
# MODE LIGNE : PostgreSQL avec traduction SQLite → PostgreSQL
# ─────────────────────────────────────────────────────────────
else:
    import psycopg2
    import psycopg2.extras

    # --- Détection des clés primaires ET des colonnes (pour INSERT OR REPLACE) ---
    # Remplis à la première connexion en interrogeant le catalogue PostgreSQL.
    _PK_CACHE = {}
    _COLS_CACHE = {}   # table -> [colonnes dans l'ordre]

    def _charger_pk(cur):
        if _PK_CACHE:
            return
        cur.execute("""
            SELECT tc.table_name, kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY'
              AND tc.table_schema = 'public'
            ORDER BY kcu.ordinal_position
        """)
        for table, col in cur.fetchall():
            _PK_CACHE.setdefault(table, []).append(col)
        # Colonnes de chaque table, dans l'ordre de déclaration
        cur.execute("""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema='public'
            ORDER BY table_name, ordinal_position
        """)
        for table, col in cur.fetchall():
            _COLS_CACHE.setdefault(table, []).append(col)

    def _clause_conflict(table):
        """Construit ' ON CONFLICT (pk) DO UPDATE SET col=EXCLUDED.col, ...'
        en connaissant les vraies colonnes de la table."""
        pk = _PK_CACHE.get(table, ["id"])
        cols = _COLS_CACHE.get(table, [])
        maj_cols = [c for c in cols if c not in pk]
        if maj_cols:
            maj = ", ".join(f"{c}=EXCLUDED.{c}" for c in maj_cols)
            return f" ON CONFLICT ({', '.join(pk)}) DO UPDATE SET {maj}"
        return f" ON CONFLICT ({', '.join(pk)}) DO NOTHING"

    def _traduire(sql):
        """Traduit une requête SQLite en PostgreSQL."""
        s = sql

        # PRAGMA : n'existe pas en PostgreSQL → requête neutre
        if re.match(r"\s*PRAGMA", s, re.I):
            return "SELECT 1"

        # sqlite_master → catalogue PostgreSQL (rare, best-effort)
        if "sqlite_master" in s.lower():
            return ("SELECT tablename AS name FROM pg_tables "
                    "WHERE schemaname='public'")

        # INSERT OR REPLACE INTO t(cols...) OU INTO t VALUES(...)
        m = re.match(r"\s*INSERT\s+OR\s+REPLACE\s+INTO\s+(\w+)\s*(\([^)]*\))?",
                     s, re.I)
        if m:
            table = m.group(1)
            cols_decl = m.group(2)   # "(a,b,c)" ou None
            s = re.sub(r"INSERT\s+OR\s+REPLACE", "INSERT", s, count=1, flags=re.I)
            pk = _PK_CACHE.get(table, ["id"])
            if cols_decl:
                # colonnes explicites → on met à jour celles-ci (sauf PK)
                cols = [c.strip() for c in cols_decl.strip("()").split(",")]
                maj = ", ".join(f"{c}=EXCLUDED.{c}" for c in cols if c not in pk)
                clause = (f" ON CONFLICT ({', '.join(pk)}) DO UPDATE SET {maj}"
                          if maj else f" ON CONFLICT ({', '.join(pk)}) DO NOTHING")
            else:
                # VALUES sans colonnes → on déduit toutes les colonnes de la table
                clause = _clause_conflict(table)
            s = s.rstrip().rstrip(";") + clause

        # INSERT OR IGNORE INTO → ON CONFLICT DO NOTHING
        m = re.match(r"\s*INSERT\s+OR\s+IGNORE\s+INTO\s+(\w+)", s, re.I)
        if m:
            table = m.group(1)
            s = re.sub(r"INSERT\s+OR\s+IGNORE", "INSERT", s, count=1, flags=re.I)
            pk = _PK_CACHE.get(table, ["id"])
            s = s.rstrip().rstrip(";") + f" ON CONFLICT ({', '.join(pk)}) DO NOTHING"

        # placeholders ? → %s  (en évitant les ? dans les chaînes '...')
        # approche simple : remplacer ? hors guillemets simples
        out, in_str = [], False
        for ch in s:
            if ch == "'":
                in_str = not in_str
            if ch == "?" and not in_str:
                out.append("%s")
            else:
                out.append(ch)
        s = "".join(out)

        # %s d'échappement PostgreSQL : les % littéraux (LIKE '%x%') doivent
        # être doublés SEULEMENT s'il y a des paramètres. psycopg2 gère cela
        # quand on passe des params ; sans params, on laisse tel quel.
        return s

    class _Cur:
        """Curseur qui traduit chaque requête avant exécution."""
        def __init__(self, raw):
            self._raw = raw
            _charger_pk(raw)

        def execute(self, sql, params=None):
            sql2 = _traduire(sql)
            has_param = params is not None
            # Doubler les % littéraux uniquement si params (sinon psycopg2 râle)
            if has_param and "%s" not in sql2 and "%" in sql2:
                sql2 = sql2.replace("%", "%%")
            self._raw.execute(sql2, params if has_param else None)
            return self

        def fetchone(self):
            return self._raw.fetchone()

        def fetchall(self):
            return self._raw.fetchall()

        @property
        def lastrowid(self):
            # PostgreSQL n'a pas lastrowid ; on tente RETURNING sinon None
            try:
                self._raw.execute("SELECT lastval()")
                return self._raw.fetchone()[0]
            except Exception:
                return None

        def __getattr__(self, name):
            return getattr(self._raw, name)

    class _Con:
        """Connexion qui imite l'API sqlite3 (execute, commit, row_factory…)."""
        def __init__(self, dsn):
            self._con = psycopg2.connect(dsn)
            self._row = False

        @property
        def row_factory(self):
            return self._row

        @row_factory.setter
        def row_factory(self, val):
            # sqlite3.Row → on utilisera un curseur dict-like
            self._row = val

        def _mkcur(self):
            if self._row:
                raw = self._con.cursor(
                    cursor_factory=psycopg2.extras.DictCursor)
            else:
                raw = self._con.cursor()
            return _Cur(raw)

        def execute(self, sql, params=None):
            cur = self._mkcur()
            cur.execute(sql, params)
            return cur

        def cursor(self):
            return self._mkcur()

        def commit(self):
            self._con.commit()

        def rollback(self):
            self._con.rollback()

        def close(self):
            self._con.close()

        def __getattr__(self, name):
            return getattr(self._con, name)

    def connect(chemin=None, **kw):
        return _Con(DATABASE_URL)

    Row = dict  # en PG, DictCursor renvoie déjà des lignes accessibles par nom
