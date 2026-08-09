#!/usr/bin/env python3
"""
ranger_downloads_v2.py — Range ~/Downloads dans les dossiers du projet, ZIPS COMPRIS.

Regles :
  1. Fichier reconnu (cartographie Yorbity ci-dessous) :
     - identique a la destination  -> CORBEILLE (~/.Trash, recuperable)
     - absent de la destination    -> DEPLACE
     - DIFFERENT de la destination -> ON N'Y TOUCHE PAS (signale : c'est
       peut-etre une version plus recente — decision humaine)
  2. Clones macOS « fichier (1).py », « fichier 2.py » : compares au meme
     titre que l'original.
  3. ZIPS : ouverts et traites membre par membre selon les memes regles
     (bruit macOS __MACOSX/.DS_Store ignore). Le zip part a la corbeille
     UNIQUEMENT si tout son contenu a ete traite ; un zip contenant du
     non-reconnu ou une version divergente reste intact.
  4. Fichier non reconnu (perso, autres projets) : JAMAIS touche.

    python scripts/ranger_downloads_v2.py --dry   # montre tout, ne fait rien
    python scripts/ranger_downloads_v2.py         # applique
"""
from __future__ import annotations

import hashlib
import io
import zipfile
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

DL = Path.home() / "Downloads"
RACINE = Path(__file__).resolve().parent.parent
CORBEILLE = Path.home() / ".Trash"
DRY = "--dry" in sys.argv

# ---------------- cartographie : motif de nom -> dossier du projet --------
CARTE = [
    # outils et patchs de la session
    (r"^(patch|sonde|installer|deployer|extraire|purger|ranger|traduire"
     r"|pretraduire|ajouter_langue|maj_registre)\w*\.py$", "scripts"),
    # adaptateurs du registre de sources
    (r"^(uk_sponsors|adzuna|mig_de|jobbank\w*|registre|base)\.py$",
     "app/api/sources"),
    # modules de l'app
    (r"^(paiement|espace|devises|i18n|pays_i18n|traduction|theme_pays"
     r"|destinations_monde|pays_monde|jobs_api|dossiers|identite|ui)\.py$",
     "app/api"),
    # donnees
    (r"^(sources_pays|uk_sponsors)\w*\.(json|csv)$", "data"),
    # rapports de session
    (r"^rapport\w*\.(md|txt)$", "docs"),
]
MOTIF_CLONE = re.compile(r"^(.*?)(?: \((\d+)\)| (\d))(\.\w+)$")


def md5_octets(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()


def md5(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def nom_canonique(nom: str) -> str:
    """« paiement (1).py » ou « paiement 2.py » -> « paiement.py »."""
    m = MOTIF_CLONE.match(nom)
    return (m.group(1) + m.group(4)) if m else nom


def destination_pour(nom: str) -> Path | None:
    for motif, dossier in CARTE:
        if re.match(motif, nom):
            return RACINE / dossier / nom
    return None


def a_la_corbeille(p: Path) -> None:
    CORBEILLE.mkdir(exist_ok=True)
    cible = CORBEILLE / p.name
    if cible.exists():
        cible = CORBEILLE / f"{p.stem}-{datetime.now():%H%M%S}{p.suffix}"
    shutil.move(str(p), str(cible))


def traiter_zip(pz: Path, ranges, corbeille, differents) -> tuple[int, bool]:
    """Traite les membres reconnus d'un zip. Retourne (nb_non_reconnus,
    tout_traite) — tout_traite=True si chaque membre reconnu a ete extrait
    ou etait deja identique (le zip devient alors jetable)."""
    inconnus, tout_traite = 0, True
    try:
        with zipfile.ZipFile(pz) as z:
            for info in z.infolist():
                nom = Path(info.filename).name
                if (info.is_dir() or not nom or nom.startswith(".")
                        or "__MACOSX" in info.filename):
                    continue
                dest = destination_pour(nom_canonique(nom))
                if dest is None:
                    inconnus += 1
                    tout_traite = False
                    continue
                contenu = z.read(info)
                if dest.exists() and md5(dest) == md5_octets(contenu):
                    corbeille.append((pz / nom, dest))          # deja la
                elif dest.exists():
                    differents.append((pz / nom, dest))
                    tout_traite = False                          # divergent
                else:
                    ranges.append((pz / nom, dest))
                    if not DRY:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(contenu)
    except zipfile.BadZipFile:
        return 1, False
    return inconnus, tout_traite


def main() -> None:
    if not DL.exists():
        print(f"Downloads introuvable : {DL}")
        sys.exit(1)
    ranges, corbeille, differents, inconnus = [], [], [], 0
    for p in sorted(DL.iterdir()):
        if not p.is_file() or p.name.startswith("."):
            continue
        if p.suffix.lower() == ".zip":
            inc, tout = traiter_zip(p, ranges, corbeille, differents)
            inconnus += inc
            if tout and not DRY:
                a_la_corbeille(p)
            if tout:
                corbeille.append((p, Path("(zip entierement traite)")))
            continue
        canon = nom_canonique(p.name)
        dest = destination_pour(canon)
        if dest is None:
            inconnus += 1
            continue
        if dest.exists() and md5(dest) == md5(p):
            corbeille.append((p, dest))
            if not DRY:
                a_la_corbeille(p)
        elif dest.exists():
            differents.append((p, dest))
        else:
            ranges.append((p, dest))
            if not DRY:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(p), str(dest))

    mode = " [DRY-RUN — rien n'a bouge]" if DRY else ""
    print(f"=== rangement de {DL}{mode} ===\n")
    for titre, liste, verbe in (
            ("RANGES (absents du projet)", ranges, "->"),
            ("CORBEILLE (identiques au projet)", corbeille, "=="),
    ):
        print(f"{titre} : {len(liste)}")
        for p, d in liste:
            ou = d.relative_to(RACINE) if d.is_absolute() else d
            print(f"  {str(p.name):42} {verbe} {ou}")
        print()
    print(f"DIFFERENTS du projet — NON touches, a arbitrer toi-meme :"
          f" {len(differents)}")
    for p, d in differents:
        if p.exists():
            age = ("plus RECENT" if p.stat().st_mtime > d.stat().st_mtime
                   else "plus ancien") + " que le projet"
        else:
            age = f"dans {p.parent.name}"
        print(f"  {str(p.name):42} ≠  {d.relative_to(RACINE)}  ({age})")
    print(f"\nnon reconnus (perso/autres projets) : {inconnus} — jamais touches")
    if DRY:
        print("\nRelance sans --dry pour appliquer.")


if __name__ == "__main__":
    main()
