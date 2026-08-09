#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collecteur_code.py — Yorbity (READ-ONLY)
========================================
Imprime le code des modules nécessaires pour :
  - caler la VRAIE taxonomie de projets (config_projets.py)
  - le patch admin (admin_projets.py + sections de ui.py)
  - le branchement traduction (traduction.py + rendu des fiches)

Usage :
    cd ~/mobilite-ia && python collecteur_code.py > code_yorbity.txt
    (puis ouvre code_yorbity.txt et colle son contenu dans Claude)
ou simplement :
    cd ~/mobilite-ia && python collecteur_code.py
"""
import os, glob, re, sys

BASE_CANDIDATS = ["app/api", "app", ".", "src"]
SEP = "=" * 70

# fichiers imprimés EN ENTIER (petits)
COMPLETS = ["config_projets.py", "admin_projets.py", "traduction.py",
            "destinations_monde.py", "services_cfg.py", "config_pays.py"]

# ui.py : on n'imprime que les sections pertinentes (fichier volumineux)
UI_MOTIFS = ("destination", "admin", "etoile", "étoile", "star", "config_pays",
             "config_projet", "traduire", "selectbox", "checkbox", "multiselect",
             "origine", "procedure", "fiche", "completer_destinations")


def base_dir():
    for b in BASE_CANDIDATS:
        if os.path.exists(os.path.join(b, "traduction.py")) or \
           os.path.exists(os.path.join(b, "ui.py")):
            return b
    return "."


def cat(path, titre=None):
    print("\n" + SEP)
    print(f"### FICHIER : {titre or path}")
    print(SEP)
    if not os.path.exists(path):
        print("(absent)")
        return
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            print(f"{i:4d}| {line.rstrip()}")


def sections_ui(path):
    print("\n" + SEP)
    print(f"### SECTIONS PERTINENTES DE : {path}")
    print(SEP)
    if not os.path.exists(path):
        print("(absent)")
        return
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    rx = re.compile("|".join(re.escape(m) for m in UI_MOTIFS), re.I)
    garder = set()
    for i, l in enumerate(lines):
        if rx.search(l):
            for j in range(max(0, i - 4), min(len(lines), i + 6)):
                garder.add(j)
    prev = -1
    for idx in sorted(garder):
        if idx != prev + 1:
            print("      …")
        print(f"{idx+1:4d}| {lines[idx].rstrip()}")
        prev = idx


def main():
    b = base_dir()
    print(SEP)
    print(f"COLLECTEUR CODE — base modules : {os.path.abspath(b)}")
    print(SEP)
    for f in COMPLETS:
        cat(os.path.join(b, f), titre=f)
    sections_ui(os.path.join(b, "ui.py"))
    print("\n" + SEP)
    print("FIN — copie TOUT ce texte dans Claude")
    print(SEP)


if __name__ == "__main__":
    main()
