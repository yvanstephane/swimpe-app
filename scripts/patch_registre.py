#!/usr/bin/env python3
"""
patch_registre.py (v2) — Branche jobs_api sur le registre de sources.

Corrections v1 -> v2 :
  * L'ancre etait `def ecran(`. La fonction d'affichage de jobs_api s'appelle
    `afficher(` ; `ecran(` est dans offres_sync. Le patch v1 s'arretait sans
    rien ecrire (comportement voulu, rien n'a ete casse).
  * Renommages par expression reguliere, insensibles aux espaces et aux
    valeurs par defaut, plutot que par egalite de chaine exacte.
  * Toutes les connexions SQLite ouvrent avec timeout=30 s.
    Le "database is locked" venait de connexions concurrentes : Streamlit
    relance le script a chaque interaction, et le mode journal par defaut
    n'autorise qu'un seul acces. Passe aussi la base en WAL :
        python -c "import sqlite3;sqlite3.connect('data/mobilite.db').execute('PRAGMA journal_mode=WAL')"

Ce que le patch fait :
  1. jobs_api : `chercher()` -> `_chercher_adzuna()`   (corps inchange)
  2. jobs_api : `couvre()`   -> `_couvre_adzuna()`
  3. jobs_api : nouvelles `chercher()` + `couvre()` branchees sur le REGISTRE,
     avec cache SQLite 12 h partage. Job Bank ouvre une page HTTP par offre :
     sans cache, chaque rerun Streamlit relancerait ~15 s de requetes.
  4. sources/registre.py : charge l'adaptateur adzuna.
  5. offres_sync : `ingerer_sources()` -> `_ingerer_sources_obsolete()`.
     La table `opportunites` n'a ni `description` ni `reference` : y pousser
     des offres leur faisait perdre ce qu'on voulait afficher.

Idempotent. Sauvegarde .bak-<horodatage>. Verifie la syntaxe, restaure si casse.

Usage :
    python scripts/patch_registre.py --dry
    python scripts/patch_registre.py
"""

from __future__ import annotations

import ast
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DRY = "--dry" in sys.argv
HORO = datetime.now().strftime("%Y%m%d-%H%M%S")

resultats: list[str] = []


def ecrire(p: Path, contenu: str, n: int) -> bool:
    if DRY:
        resultats.append(f"~ {p.name} : {n} patch(s) [DRY-RUN]")
        return True
    bak = p.with_suffix(p.suffix + f".bak-{HORO}")
    shutil.copy2(p, bak)
    p.write_text(contenu, encoding="utf-8")
    try:
        ast.parse(contenu)
    except SyntaxError as e:
        shutil.copy2(bak, p)
        resultats.append(f"x {p.name} : SYNTAXE CASSEE ligne {e.lineno} — restaure")
        return False
    resultats.append(f"v {p.name} : {n} patch(s), syntaxe OK ({bak.name})")
    return True


# --------------------------------------------------------------------------- #
BLOC = '''

# --- ajoute par patch_registre.py ------------------------------------------
def _cx(timeout=30):
    """Connexion SQLite tolerante aux acces concurrents (Streamlit reruns)."""
    con = sqlite3.connect(DB, timeout=timeout)
    try:
        con.execute("PRAGMA busy_timeout=30000")
    except Exception:
        pass
    return con


def _cache_lire(cle, heures=CACHE_HEURES):
    _init()
    con = _cx()
    con.row_factory = sqlite3.Row
    try:
        row = con.execute("SELECT * FROM jobs_cache WHERE cle=?", (cle,)).fetchone()
    finally:
        con.close()
    if not row:
        return None
    try:
        age = datetime.datetime.now() - datetime.datetime.fromisoformat(row["maj"])
        if age.total_seconds() < heures * 3600:
            return json.loads(row["contenu"])
    except Exception:
        pass
    return None


def _cache_ecrire(cle, dest, type_projet, offres):
    _init()
    con = _cx()
    try:
        con.execute(
            "INSERT OR REPLACE INTO jobs_cache(cle,dest,type,contenu,maj) "
            "VALUES(?,?,?,?,?)",
            (cle, dest, type_projet, json.dumps(offres, ensure_ascii=False),
             datetime.datetime.now().isoformat(timespec="seconds")))
        con.commit()
    finally:
        con.close()


def chercher(dest_code, type_projet, domaine=""):
    """
    Offres en direct, TOUTES SOURCES (registre : Adzuna + Job Bank + futures).
    Cache 12 h. Repli sur Adzuna seul si le registre est indisponible.
    """
    cle = f"all:{dest_code.upper()}:{type_projet}:{domaine[:20]}"
    cache = _cache_lire(cle)
    if cache is not None:
        return cache

    try:
        from sources import registre
        offres = registre.collecter(dest_code, type_projet,
                                    mots_cles=domaine or None, limite=MAX_OFFRES)
    except Exception as e:
        print("registre indisponible, repli Adzuna seul :", e)
        offres = _chercher_adzuna(dest_code, type_projet, domaine) or []

    offres = [o for o in offres if not _bruit(o)]
    try:
        _cache_ecrire(cle, dest_code.upper(), type_projet, offres)
    except Exception as e:
        print("cache non ecrit :", e)
    return offres


def couvre(dest_code):
    """Vrai si AU MOINS une source du registre couvre cette destination."""
    if dest_code.upper() in PAYS_ADZUNA:
        return True
    try:
        from sources import registre
        return dest_code.upper() in registre.destinations_couvertes()
    except Exception:
        return False
# ---------------------------------------------------------------------------
'''

RE_CHERCHER = re.compile(r"^def\s+chercher\s*\(", re.M)
RE_COUVRE = re.compile(r"^def\s+couvre\s*\(", re.M)
RE_ANCRE = re.compile(r"^def\s+(afficher|ecran)\s*\(", re.M)


def patch_jobs_api() -> None:
    p = RACINE / "app" / "api" / "jobs_api.py"
    if not p.exists():
        resultats.append("- jobs_api.py introuvable")
        return
    src = p.read_text(encoding="utf-8")

    if "_chercher_adzuna" in src:
        resultats.append("= jobs_api.py : deja patche")
        return

    m = RE_ANCRE.search(src)
    if not m:
        resultats.append("? jobs_api.py : ni def afficher( ni def ecran( — abandon")
        return

    n = 0
    if RE_CHERCHER.search(src):
        src = RE_CHERCHER.sub("def _chercher_adzuna(", src, count=1)
        n += 1
    else:
        resultats.append("? jobs_api.py : def chercher( introuvable — abandon")
        return

    if RE_COUVRE.search(src):
        src = RE_COUVRE.sub("def _couvre_adzuna(", src, count=1)
        n += 1

    m = RE_ANCRE.search(src)  # position recalculee apres substitutions
    src = src[:m.start()] + BLOC.lstrip("\n") + "\n" + src[m.start():]
    n += 1

    ecrire(p, src, n)


def patch_registre() -> None:
    p = RACINE / "app" / "api" / "sources" / "registre.py"
    if not p.exists():
        resultats.append("- sources/registre.py introuvable")
        return
    src = p.read_text(encoding="utf-8")
    if re.search(r"^\s*from \. import adzuna", src, re.M):
        resultats.append("= registre.py : adzuna deja charge")
        return
    src = src.replace(
        "    # from . import adzuna    # a decommenter une fois ecrit",
        "    from . import adzuna      # noqa: F401", 1)
    if not re.search(r"^\s*from \. import adzuna", src, re.M):
        src = src.replace(
            "    from . import jobbank_ca  # noqa: F401",
            "    from . import jobbank_ca  # noqa: F401\n"
            "    from . import adzuna      # noqa: F401", 1)
    if not re.search(r"^\s*from \. import adzuna", src, re.M):
        resultats.append("? registre.py : point d'insertion introuvable")
        return
    ecrire(p, src, 1)


def patch_offres_sync() -> None:
    p = RACINE / "app" / "api" / "offres_sync.py"
    if not p.exists():
        resultats.append("- offres_sync.py introuvable")
        return
    src = p.read_text(encoding="utf-8")
    if "_ingerer_sources_obsolete" in src:
        resultats.append("= offres_sync.py : deja neutralise")
        return
    if not re.search(r"^def\s+ingerer_sources\s*\(", src, re.M):
        resultats.append("= offres_sync.py : ingerer_sources() absente, rien a faire")
        return
    src = re.sub(r"^def\s+ingerer_sources\s*\(",
                 "def _ingerer_sources_obsolete(", src, count=1, flags=re.M)
    ecrire(p, src, 1)


# --------------------------------------------------------------------------- #
def main() -> None:
    if DRY:
        print(">>> DRY-RUN : rien ne sera ecrit\n")
    patch_jobs_api()
    patch_registre()
    patch_offres_sync()

    print()
    for r in resultats:
        print(" ", r)
    print()
    if any(r.startswith("x") for r in resultats):
        print("ECHEC : fichier restaure. Rien n'est casse.")
        sys.exit(1)
    if any(r.startswith("?") for r in resultats):
        print("ATTENTION : au moins une ancre est introuvable. Rien n'a ete ecrit")
        print("pour ce fichier. Envoie-moi la sortie.")
        sys.exit(2)
    print("FINI. Vide le cache puis relance :")
    print("  python -c \"import sqlite3;c=sqlite3.connect('data/mobilite.db',timeout=30);"
          "c.execute('DELETE FROM jobs_cache');c.commit();print('cache vide')\"")
    print("  yorbity")


if __name__ == "__main__":
    main()
