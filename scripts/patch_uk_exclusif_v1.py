#!/usr/bin/env python3
"""
patch_uk_exclusif_v1.py — Le Royaume-Uni devient le domaine EXCLUSIF de
uk_sponsors (Adzuna gb ∩ registre des sponsors, liens Find a Job).

PREUVE (capture 2026-07-10, ref JOB-5715041459) : l'Adzuna generique
couvre aussi GB et empile SES copies des offres — liens click.appcast.io
geo-bloques — apres celles des sponsors. Un clic dessus = « This job is
not available in your area », meme pour l'admin.

CORRECTIF : GB retire des destinations de l'adaptateur Adzuna generique.
Resultat sur la page Royaume-Uni : uniquement des references UKS-,
uniquement des liens findajob.dwp.gov.uk, zero doublon.

Idempotent. Sauvegarde .bak. Syntaxe verifiee, restauration si casse.
Usage : python scripts/patch_uk_exclusif_v1.py [--dry]
"""
from __future__ import annotations

import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DRY = "--dry" in sys.argv
P = RACINE / "app" / "api" / "sources" / "adzuna.py"

ANCIEN = '''DESTINATIONS = ("FR", "GB", "CA", "DE", "US", "IT", "ES", "NL", "AT", "BE",
                "CH", "AU", "NZ", "BR", "IN", "MX", "PL", "SG", "ZA")'''
NOUVEAU = '''# GB retire (patch_uk_exclusif) : le Royaume-Uni est servi EXCLUSIVEMENT
# par uk_sponsors (registre Home Office + liens Find a Job accessibles
# partout). L'Adzuna generique n'y ajoutait que des doublons aux liens
# click.appcast.io geo-bloques.
DESTINATIONS = ("FR", "CA", "DE", "US", "IT", "ES", "NL", "AT", "BE",
                "CH", "AU", "NZ", "BR", "IN", "MX", "PL", "SG", "ZA")'''


def main() -> None:
    src = P.read_text(encoding="utf-8")
    if "patch_uk_exclusif" in src:
        print("= adzuna.py : GB deja exclu")
        return
    if ANCIEN not in src:
        print("? adzuna.py : tuple DESTINATIONS introuvable a l'identique")
        sys.exit(2)
    if DRY:
        print("~ adzuna.py : 1 retouche [DRY-RUN]")
        return
    nouveau = src.replace(ANCIEN, NOUVEAU, 1)
    ast.parse(nouveau)
    bak = P.with_suffix(f".py.bak-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(P, bak)
    P.write_text(nouveau, encoding="utf-8")
    print(f"v adzuna.py : GB exclu ({bak.name})")


if __name__ == "__main__":
    main()
