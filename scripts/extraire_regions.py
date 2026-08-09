#!/usr/bin/env python3
"""
extraire_regions.py — Imprime les 3 regions de code dont j'ai besoin pour
ecrire patch_accompagnement.py sans travailler a l'aveugle.

Lecture seule. Ne modifie rien.
Usage : python scripts/extraire_regions.py
Puis colle TOUTE la sortie dans la conversation.
"""
from __future__ import annotations

from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent

CIBLES = [
    # (fichier, etiquette, motif, lignes avant, lignes apres)
    ("app/api/ui.py", "HAUT-DE-FICHIER", "set_page_config", 3, 15),
    ("app/api/ui.py", "SERVICES-DEBUT", "On t'accompagne jusqu'en", 3, 45),
    ("app/api/ui.py", "SERVICES-FIN", "Parle-nous de ton projet", 5, 12),
    ("app/api/ui.py", "BANNIERE-PRIX", "Commence ton projet", 6, 20),
    # replis si la banniere / les services vivent ailleurs
    ("app/api/opportunites_ui.py", "BANNIERE-PRIX (repli)", "Commence ton projet", 6, 20),
    ("app/api/opportunites_ui.py", "SERVICES (repli)", "On t'accompagne jusqu'en", 3, 45),
]


def montrer(fichier: str, etiquette: str, motif: str, avant: int, apres: int) -> None:
    p = RACINE / fichier
    if not p.exists():
        return
    lignes = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    trouves = [i for i, l in enumerate(lignes) if motif in l]
    if not trouves:
        print(f"===== {etiquette} : motif {motif!r} ABSENT de {fichier} =====\n")
        return
    for i in trouves:
        deb, fin = max(0, i - avant), min(len(lignes), i + apres + 1)
        print(f"===== {etiquette} — {fichier} lignes {deb + 1}-{fin} =====")
        for j in range(deb, fin):
            marque = ">>" if j == i else "  "
            print(f"{marque}{j + 1:5d}| {lignes[j]}")
        print()


def main() -> None:
    print("Colle l'INTEGRALITE de cette sortie dans la conversation.\n")
    for cible in CIBLES:
        montrer(*cible)
    print("===== FIN =====")


if __name__ == "__main__":
    main()
