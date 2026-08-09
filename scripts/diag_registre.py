#!/usr/bin/env python3
"""
diag_registre.py — Pourquoi Job Bank n'apparait pas sous "Metier specialise" ?

Trois hypotheses, testees hors Streamlit :

  (a) MOT-CLE POLLUE. jobs_api.chercher() passe `mots_cles=domaine or None`.
      Si l'UI envoie "Tous secteurs" ou un domaine francais, cela devient
      dkw="Tous secteurs" -> 0 resultat. Adzuna filtre "tous"/"all" dans
      _mots() ; l'adaptateur Job Bank ne le faisait pas.

  (b) CACHE VIDE FIGE. _cache_ecrire() ecrit meme une liste vide.
      Un premier rendu rate met [] en cache pour 12 h.

  (c) EXCEPTION AVALEE. registre.collecter() attrape les erreurs de source
      et les log en `error` — invisible depuis Streamlit.

Lecture seule, sauf --vider-cache.
Usage :
    python scripts/diag_registre.py
    python scripts/diag_registre.py --vider-cache
"""
from __future__ import annotations

import logging
import sqlite3
import sys
import traceback
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "app" / "api"))
sys.path.insert(0, str(RACINE))
DB = RACINE / "data" / "mobilite.db"

logging.basicConfig(level=logging.INFO, format="    %(levelname)s %(message)s")


def titre(t):
    print("\n" + "=" * 72 + "\n" + t + "\n" + "=" * 72)


# --------------------------------------------------------------------------- #
titre("1. Le registre est-il importable ?")
try:
    from sources import registre
    print("  OK — sources :", list(registre.toutes()))
except Exception:
    print("  ECHEC. C'est la cause : jobs_api retombe sur Adzuna seul.")
    traceback.print_exc()
    sys.exit(1)


titre("2. Sources actives, routage CA / metier")
for nom in registre.toutes():
    print(f"  {nom:14} active={registre.est_active(nom)}")

srcs = registre.sources_pour("CA", "metier")
print("\n  sources_pour('CA','metier') ->", [s.nom for s in srcs] or "AUCUNE")
for s in srcs:
    print(f"    {s.nom:14} disponible={s.disponible()} "
          f"sans_permis={s.admissible_sans_permis('CA','metier')}")

if not any(s.nom == "jobbank_ca" for s in srcs):
    print("\n  >>> jobbank_ca ABSENT du routage. Cause trouvee. Fin.")
    sys.exit(0)


# --------------------------------------------------------------------------- #
titre("3. Hypothese (a) : le mot-cle tue-t-il la requete ?")
from sources import jobbank_ca as jb

src = registre.par_nom("jobbank_ca")
essais = [
    ("aucun mot-cle (None)", None),
    ("'Tous secteurs' (ce que l'UI envoie peut-etre)", "Tous secteurs"),
    ("'tous secteurs' minuscule", "tous secteurs"),
    ("'carpenter' (anglais, pertinent)", "carpenter"),
    ("'menuisier' (francais sur flux EN)", "menuisier"),
]
for libelle, mots in essais:
    try:
        n = len(src._liste(src._params("metier", mots, 8, "en"), 25))
        print(f"  {n:>3} resultat(s)   dkw={mots!r:42} {libelle}")
    except Exception as e:
        print(f"  ERR              dkw={mots!r:42} {e}")


# --------------------------------------------------------------------------- #
titre("4. Hypothese (c) : collecter() leve-t-il ?")
try:
    offres = src.collecter("CA", "metier", mots_cles=None, limite=3)
    print(f"  collecter(mots_cles=None, limite=3) -> {len(offres)} offre(s)")
    for o in offres:
        print(f"    - {o.titre[:40]:42} {o.entreprise[:24]:26} {o.reference}")
except Exception:
    print("  EXCEPTION — c'est la cause (c).")
    traceback.print_exc()


# --------------------------------------------------------------------------- #
titre("5. Hypothese (b) : le cache contient-il du vide ?")
if not DB.exists():
    print("  base introuvable")
else:
    con = sqlite3.connect(DB, timeout=30)
    rows = con.execute(
        "SELECT cle, length(contenu), maj FROM jobs_cache WHERE cle LIKE 'all:%'"
    ).fetchall()
    if not rows:
        print("  aucune entree 'all:*' — le cache n'a jamais ete ecrit")
    for cle, taille, maj in rows:
        vide = "  <<< VIDE" if taille is not None and taille <= 2 else ""
        print(f"  {cle:44} {taille:>6} octets  {maj}{vide}")

    if "--vider-cache" in sys.argv:
        n = con.execute("DELETE FROM jobs_cache").rowcount
        con.commit()
        print(f"\n  cache vide : {n} entree(s) supprimee(s)")
    con.close()


# --------------------------------------------------------------------------- #
titre("6. Ce que jobs_api.chercher() envoie reellement")
print("  Regarde app/api/jobs_api.py, dans la nouvelle chercher() :")
print("    registre.collecter(dest_code, type_projet, mots_cles=domaine or None, ...)")
print("  Si `domaine` vaut 'Tous secteurs', dkw='Tous secteurs' -> 0 offre.")
print("  Compare avec le nombre de resultats de l'etape 3.")
