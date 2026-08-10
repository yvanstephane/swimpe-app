#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
db.py — Couche de compatibilité base de données pour Swimpe (v3 PARESSEUSE)
===========================================================================
Décision SQLite/PostgreSQL prise À CHAQUE connexion (pas au chargement).
Cela règle le problème de timing Streamlit : au démarrage, st.secrets n'est
pas prêt ; à la 1re connexion réelle (auth.init_db), il l'est.

  - Local (pas de DATABASE_URL)  → SQLite pur.
  - En ligne (DATABASE_URL présent, env OU st.secrets) → PostgreSQL + traduction.

L'API imite sqlite3 : connect(), Row, execute/fetch, row_factory, lastrowid.
"""
import os
import re
import sqlite3 as _sqlite_top

# Capture de la fonction connect ORIGINALE de sqlite3, faite au tout premier
# import de db.py. Si un fichier a deja stocke l'original dans _connect_origine
# (parce qu'il a deja redirige), on le reutilise ; sinon on prend connect tel
# quel (encore vierge). Dans tous les cas on obtient le vrai connect natif.
_ORIG_CONNECT = getattr(_sqlite_top, "_connect_origine", None) or _sqlite_top.connect

_PK_CACHE = {}
_COLS_CACHE = {}


def _resoudre_database_url():
    """Lit DATABASE_URL depuis os.environ OU st.secrets (et propage les secrets)."""
    u = os.environ.get("DATABASE_URL", "").strip()
    if u:
        return u
    try:
        import streamlit as _st
        if hasattr(_st, "secrets"):
            # propage tous les secrets vers os.environ (une fois)
            try:
                for _k in list(_st.secrets.keys()):
                    if _k not in os.environ:
                        os.environ[_k] = str(_st.secrets[_k])
            except Exception:
                pass
            v = os.environ.get("DATABASE_URL", "").strip()
            if v:
                return v
            if "DATABASE_URL" in _st.secrets:
                return str(_st.secrets["DATABASE_URL"]).strip()
    except Exception:
        pass
    return ""


def _mode_pg():
    """True si on doit parler PostgreSQL, évalué à CHAQUE appel."""
    return bool(_resoudre_database_url())


# Compat : certains fichiers lisent db.MODE_PG au chargement. On expose une
# valeur initiale, mais la vraie décision se prend dans connect() (paresseux).
MODE_PG = _mode_pg()


# ─────────────────────────── SQLite (local) ───────────────────────────
import sqlite3 as _sqlite

def _connect_sqlite(chemin="data/mobilite.db", **kw):
    kw.setdefault("timeout", 30)
    # _ORIG_CONNECT = le vrai connect natif (capture en haut du module),
    # JAMAIS le connect redirige, donc pas de recursion.
    con = _ORIG_CONNECT(chemin, **kw)
    try:
        con.execute("PRAGMA busy_timeout=30000")
    except Exception:
        pass
    return con


# ─────────────────────── PostgreSQL (en ligne) ───────────────────────
def _charger_pk(cur):
    if _PK_CACHE:
        return
    cur.execute("""
        SELECT tc.table_name, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type='PRIMARY KEY' AND tc.table_schema='public'
        ORDER BY kcu.ordinal_position""")
    for table, col in cur.fetchall():
        _PK_CACHE.setdefault(table, []).append(col)
    cur.execute("""
        SELECT table_name, column_name FROM information_schema.columns
        WHERE table_schema='public' ORDER BY table_name, ordinal_position""")
    for table, col in cur.fetchall():
        _COLS_CACHE.setdefault(table, []).append(col)


def _clause_conflict(table):
    pk = _PK_CACHE.get(table, ["id"])
    cols = _COLS_CACHE.get(table, [])
    maj = [c for c in cols if c not in pk]
    if maj:
        s = ", ".join(f"{c}=EXCLUDED.{c}" for c in maj)
        return f" ON CONFLICT ({', '.join(pk)}) DO UPDATE SET {s}"
    return f" ON CONFLICT ({', '.join(pk)}) DO NOTHING"


def _traduire(sql):
    s = sql
    if re.match(r"\s*PRAGMA", s, re.I):
        return "SELECT 1"
    if "sqlite_master" in s.lower():
        return "SELECT tablename AS name FROM pg_tables WHERE schemaname='public'"
    m = re.match(r"\s*INSERT\s+OR\s+REPLACE\s+INTO\s+(\w+)\s*(\([^)]*\))?", s, re.I)
    if m:
        table, cols_decl = m.group(1), m.group(2)
        s = re.sub(r"INSERT\s+OR\s+REPLACE", "INSERT", s, count=1, flags=re.I)
        pk = _PK_CACHE.get(table, ["id"])
        if cols_decl:
            cols = [c.strip() for c in cols_decl.strip("()").split(",")]
            maj = ", ".join(f"{c}=EXCLUDED.{c}" for c in cols if c not in pk)
            clause = (f" ON CONFLICT ({', '.join(pk)}) DO UPDATE SET {maj}"
                      if maj else f" ON CONFLICT ({', '.join(pk)}) DO NOTHING")
        else:
            clause = _clause_conflict(table)
        s = s.rstrip().rstrip(";") + clause
    m = re.match(r"\s*INSERT\s+OR\s+IGNORE\s+INTO\s+(\w+)", s, re.I)
    if m:
        table = m.group(1)
        s = re.sub(r"INSERT\s+OR\s+IGNORE", "INSERT", s, count=1, flags=re.I)
        pk = _PK_CACHE.get(table, ["id"])
        s = s.rstrip().rstrip(";") + f" ON CONFLICT ({', '.join(pk)}) DO NOTHING"
    out, in_str = [], False
    for ch in s:
        if ch == "'":
            in_str = not in_str
        out.append("%s" if (ch == "?" and not in_str) else ch)
    return "".join(out)


class _Cur:
    def __init__(self, raw):
        self._raw = raw
        _charger_pk(raw)
    def execute(self, sql, params=None):
        sql2 = _traduire(sql)
        has = params is not None
        if has and "%s" not in sql2 and "%" in sql2:
            sql2 = sql2.replace("%", "%%")
        self._raw.execute(sql2, params if has else None)
        return self
    def fetchone(self): return self._raw.fetchone()
    def fetchall(self): return self._raw.fetchall()
    @property
    def lastrowid(self):
        try:
            self._raw.execute("SELECT lastval()")
            return self._raw.fetchone()[0]
        except Exception:
            return None
    def __getattr__(self, n): return getattr(self._raw, n)


class _Con:
    def __init__(self, dsn):
        import psycopg2
        self._psycopg2 = psycopg2
        self._con = psycopg2.connect(dsn)
        self._row = False
    @property
    def row_factory(self): return self._row
    @row_factory.setter
    def row_factory(self, v): self._row = v
    def _mkcur(self):
        import psycopg2.extras
        if self._row:
            return _Cur(self._con.cursor(cursor_factory=psycopg2.extras.DictCursor))
        return _Cur(self._con.cursor())
    def execute(self, sql, params=None):
        c = self._mkcur(); c.execute(sql, params); return c
    def cursor(self): return self._mkcur()
    def commit(self): self._con.commit()
    def rollback(self): self._con.rollback()
    def close(self): self._con.close()
    def __getattr__(self, n): return getattr(self._con, n)


# ─────────────────────────── API publique ───────────────────────────
class _RowFactoryProxy:
    """Row qui marche dans les deux modes."""
    def __call__(self, *a, **k):
        return _sqlite.Row(*a, **k)

Row = _sqlite.Row  # en PG, DictCursor gère déjà l'accès par nom


def connect(chemin="data/mobilite.db", *args, **kwargs):
    """DÉCISION PARESSEUSE : PostgreSQL si DATABASE_URL dispo, sinon SQLite."""
    dsn = _resoudre_database_url()
    if dsn:
        con = _Con(dsn)
        con.row_factory = False  # sera mis à Row par le code appelant si besoin
        return con
    return _connect_sqlite(chemin, **{k: v for k, v in kwargs.items()
                                       if k in ("timeout", "check_same_thread",
                                                "detect_types", "isolation_level")})
