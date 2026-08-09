#!/usr/bin/env python3
"""
extraire_comptes.py — Regions necessaires au VERROU NOMINATIF :
« un abonne ne cree des dossiers que pour lui-meme ».

Imprime :
  1. le schema SQL des tables users et dossiers (la verite du stockage)
  2. auth.py     : signatures + region du formulaire d'inscription
  3. espace.py   : signatures (qui est connecte ? est_admin ?)
  4. dossiers.py : signatures + region de creation d'un dossier
  5. ui.py       : les appels a dossiers./espace. avec contexte

Lecture seule. Usage : python scripts/extraire_comptes.py > comptes.txt
Puis glisse comptes.txt dans la conversation.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
API = RACINE / "app" / "api"
DB = RACINE / "data" / "mobilite.db"


def titre(t):
    print("\n" + "#" * 70 + f"\n# {t}\n" + "#" * 70 + "\n")


def bloc(lignes, i, avant, apres):
    for j in range(max(0, i - avant), min(len(lignes), i + apres + 1)):
        m = ">>" if j == i else "  "
        print(f"{m}{j + 1:5d}| {lignes[j]}")
    print()


def montrer(nom, motifs, avant=3, apres=22, max_hits=2):
    p = API / nom
    if not p.exists():
        print(f"[absent] {nom}\n")
        return
    lignes = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    # signatures d'abord
    print(f"--- {nom} : signatures ---")
    for j, l in enumerate(lignes):
        if re.match(r"\s*def \w+", l):
            print(f"{j + 1:5d}| {l}")
    print()
    vus = set()
    for motif in motifs:
        hits = [i for i, l in enumerate(lignes) if motif in l and i not in vus]
        for i in hits[:max_hits]:
            for k in range(max(0, i - avant), min(len(lignes), i + apres + 1)):
                vus.add(k)
            print(f"--- {nom} : {motif!r} ---")
            bloc(lignes, i, avant, apres)


def main():
    print("Glisse ce fichier (comptes.txt) dans la conversation.\n")

    titre("1. Schemas SQL : users, dossiers")
    if DB.exists():
        con = sqlite3.connect(DB, timeout=10)
        for table in ("users", "dossiers", "leads"):
            row = con.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                (table,)).fetchone()
            print(f"-- {table}:")
            print((row[0] if row else "  (absente)") + "\n")
        con.close()
    else:
        print("base absente\n")

    titre("2. auth.py — inscription")
    montrer("auth.py", ["inscription", "register", "s'inscrire", "S'inscrire",
                        "nom", "INSERT INTO users"])

    titre("3. espace.py — session / admin")
    montrer("espace.py", ["est_admin", "session_state", "user", "email"],
            apres=12)

    titre("4. dossiers.py — creation")
    montrer("dossiers.py", ["INSERT INTO dossiers", "creer", "nouveau",
                            "nom", "prenom"])

    titre("5. ui.py — appels dossiers/espace")
    montrer("ui.py", ["dossiers.", "espace.utilisateur", "espace.email",
                      "espace.connecte"], apres=10, max_hits=3)

    print("===== FIN =====")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        pass
