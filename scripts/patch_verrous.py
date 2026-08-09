#!/usr/bin/env python3
"""
patch_verrous.py — Fin des « database is locked », une bonne fois pour toutes.

DIAGNOSTIC
  Une dizaine de modules (auth, dossiers, services_cfg, devises_cfg,
  offres_sync, jobs_api...) ouvrent sqlite3.connect("data/mobilite.db")
  SANS timeout. Le defaut de Python est 5 s, mais surtout : quand deux
  choses ecrivent en meme temps (deux instances Streamlit, un rerun pendant
  une ecriture de cache...), la connexion sans patience leve immediatement
  « database is locked ».

TRAITEMENT AU POINT UNIQUE
  Corriger chaque module serait sans fin — la meme classe de probleme que
  le KeyError de langue. On installe, tout en haut de ui.py (avant que le
  moindre module n'ouvre une connexion), un ENROBAGE GLOBAL de
  sqlite3.connect : toute connexion du processus recoit timeout=30 s et
  busy_timeout=30 s, sauf si l'appelant en precise un lui-meme.
  Tous les modules — presents et futurs — en beneficient sans etre touches.

  Ce que ca ne repare pas (et ne peut pas) : DEUX instances Streamlit qui
  se battent en ecriture. Le patch rend l'attente patiente au lieu de
  planter, mais garde l'hygiene : pkill -f streamlit avant de relancer.

Idempotent. Sauvegarde .bak. Syntaxe verifiee, restauration si casse.
Usage : python scripts/patch_verrous.py [--dry]
"""
from __future__ import annotations

import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DRY = "--dry" in sys.argv
P = RACINE / "app" / "api" / "ui.py"

ANCRE = "import sqlite3, os, datetime"

BLOC = '''import sqlite3, os, datetime

# --- Verrous SQLite : patience globale (patch_verrous) ------------------------
# Toute connexion ouverte par N'IMPORTE QUEL module de ce processus recoit
# timeout=30 s + busy_timeout=30 s (sauf timeout explicite de l'appelant).
# Streamlit relance ce script a chaque interaction : les acces concurrents
# attendent leur tour au lieu de lever « database is locked ».
if not getattr(sqlite3, "_yorbity_patience", False):
    _sq_connect_origine = sqlite3.connect

    def _sq_connect_patient(*args, **kwargs):
        kwargs.setdefault("timeout", 30)
        con = _sq_connect_origine(*args, **kwargs)
        try:
            con.execute("PRAGMA busy_timeout=30000")
        except Exception:
            pass
        return con

    sqlite3.connect = _sq_connect_patient
    sqlite3._yorbity_patience = True
# ------------------------------------------------------------------------------'''


def main() -> None:
    if not P.exists():
        print("ui.py introuvable")
        sys.exit(1)
    src = P.read_text(encoding="utf-8")
    if "_yorbity_patience" in src:
        print("= ui.py : patience SQLite deja en place")
        return
    if ANCRE not in src:
        print("? ui.py : ancre `import sqlite3, os, datetime` introuvable")
        sys.exit(2)
    if DRY:
        print("~ ui.py : 1 retouche [DRY-RUN]")
        return
    nouveau = src.replace(ANCRE, BLOC, 1)
    try:
        ast.parse(nouveau)
    except SyntaxError as e:
        print(f"x syntaxe cassee l.{e.lineno} — rien ecrit")
        sys.exit(1)
    bak = P.with_suffix(f".py.bak-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(P, bak)
    P.write_text(nouveau, encoding="utf-8")
    print(f"v ui.py : patience SQLite installee ({bak.name})")
    print("Hygiene : toujours pkill -f streamlit avant de relancer.")


if __name__ == "__main__":
    main()
