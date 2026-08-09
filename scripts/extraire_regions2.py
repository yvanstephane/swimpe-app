#!/usr/bin/env python3
"""
extraire_regions2.py — Version 2, consciente de l'architecture i18n.

Le v1 cherchait les TEXTES affiches ("On t'accompagne...") dans ui.py.
Rate : ui.py utilise des CLES courtes — t("langue_label", LG) — et les
textes vivent dans le dictionnaire T de i18n.py.

Ce v2 procede en deux passes :
  1. i18n.py : trouve les lignes contenant les textes cibles -> les noms
     de cles apparaissent sur ces lignes.
  2. ui.py : imprime chaque usage de ces cles (et des modules lies) avec
     leur contexte.
Imprime aussi devises_cfg.py (module devise EXISTANT, a ne pas doublonner)
et les usages de services_cfg.

Lecture seule. Usage : python scripts/extraire_regions2.py
Colle TOUTE la sortie.
"""
from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
API = RACINE / "app" / "api"

TEXTES_CIBLES = [
    "On t'accompagne",
    "Parle-nous de ton projet",
    "Commence ton projet",
    "à partir de",
]

MAX_LIGNES_FICHIER = 140


def lire(nom: str) -> list[str] | None:
    p = API / nom
    if not p.exists():
        print(f"[absent] {nom}\n")
        return None
    return p.read_text(encoding="utf-8", errors="ignore").splitlines()


def bloc(lignes: list[str], centre: int, avant: int, apres: int,
         marque: int | None = None) -> None:
    deb, fin = max(0, centre - avant), min(len(lignes), centre + apres + 1)
    for j in range(deb, fin):
        m = ">>" if j == (marque if marque is not None else centre) else "  "
        print(f"{m}{j + 1:5d}| {lignes[j]}")
    print()


def main() -> None:
    print("Colle l'INTEGRALITE de cette sortie.\n")

    # ------------------------------------------------------------------ 1
    print("#" * 70)
    print("# PASSE 1 — i18n.py : ou vivent les textes, et sous quelles cles")
    print("#" * 70 + "\n")
    i18n = lire("i18n.py")
    cles_candidates: set[str] = set()
    if i18n:
        for texte in TEXTES_CIBLES:
            hits = [i for i, l in enumerate(i18n) if texte in l]
            if not hits:
                print(f"----- {texte!r} : ABSENT de i18n.py -----\n")
                continue
            for i in hits[:3]:
                print(f"----- {texte!r} -> i18n.py -----")
                bloc(i18n, i, 3, 3)
                # noms de cles plausibles sur la ligne et 3 lignes au-dessus
                for j in range(max(0, i - 3), i + 1):
                    for m in re.finditer(r'["\'](\w{3,40})["\']\s*:', i18n[j]):
                        cles_candidates.add(m.group(1))

    cles_candidates |= {"accompagne", "parle", "commence", "pitch",
                        "bandeau", "banniere", "svc", "service"}
    print(f"Cles/candidats a traquer dans ui.py : {sorted(cles_candidates)}\n")

    # ------------------------------------------------------------------ 2
    print("#" * 70)
    print("# PASSE 2 — ui.py : usages de ces cles + _PITCH_PROJET + modules")
    print("#" * 70 + "\n")
    ui = lire("ui.py")
    if ui:
        vus: set[int] = set()

        def dump(motif: str, avant=4, apres=18, max_hits=3):
            hits = [i for i, l in enumerate(ui) if motif in l and i not in vus]
            for i in hits[:max_hits]:
                for k in range(max(0, i - avant), min(len(ui), i + apres + 1)):
                    vus.add(k)
                print(f"----- ui.py : {motif!r} -----")
                bloc(ui, i, avant, apres)

        for cle in sorted(cles_candidates):
            dump(cle, avant=3, apres=14, max_hits=2)
        dump("_PITCH_PROJET", avant=3, apres=22)
        dump("devises_cfg.", avant=3, apres=10, max_hits=4)
        dump("services_cfg.", avant=3, apres=14, max_hits=4)

    # ------------------------------------------------------------------ 3
    print("#" * 70)
    print("# PASSE 3 — devises_cfg.py (module devise existant)")
    print("#" * 70 + "\n")
    dc = lire("devises_cfg.py")
    if dc:
        if len(dc) <= MAX_LIGNES_FICHIER:
            for j, l in enumerate(dc):
                print(f"{j + 1:5d}| {l}")
        else:
            print(f"(fichier long : {len(dc)} lignes — tete + signatures)\n")
            for j in range(60):
                print(f"{j + 1:5d}| {dc[j]}")
            print("  ...")
            for j, l in enumerate(dc):
                if re.match(r"\s*def \w+", l):
                    print(f"{j + 1:5d}| {l}")
        print()

    # ------------------------------------------------------------------ 4
    print("#" * 70)
    print("# PASSE 4 — services_cfg.py (signatures + tete)")
    print("#" * 70 + "\n")
    sc = lire("services_cfg.py")
    if sc:
        for j in range(min(40, len(sc))):
            print(f"{j + 1:5d}| {sc[j]}")
        print("  ...")
        for j, l in enumerate(sc):
            if re.match(r"\s*def \w+", l) and j >= 40:
                print(f"{j + 1:5d}| {l}")
        print()

    print("===== FIN =====")


if __name__ == "__main__":
    main()
