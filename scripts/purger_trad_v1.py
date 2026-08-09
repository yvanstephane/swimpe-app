#!/usr/bin/env python3
"""
purger_trad_v1.py — Nettoie le cache de traduction des entrees polluees.

  python scripts/purger_trad_v1.py de it              # purge TOUT de+it
  python scripts/purger_trad_v1.py de it --polluees   # + les entrees
        d'autres langues restees en francais (heuristique : marqueurs
        exclusivement francais — vous, tes, aux, avec, pour, c'est...)
  ... --dry            # montre sans supprimer

Pourquoi purger de/it EN ENTIER : toutes leurs entrees ont ete produites
avec le prompt casse (« vers le de ») — suspectes en bloc. Les entrees
supprimees seront retraduites a la volee, avec le prompt verrouille du
fixpack. Sauvegarde prealable de la table dans data/trad_cache_bak.json.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DB = RACINE / "data" / "mobilite.db"

_STOP_FR = (" vous ", " tes ", " c'est ", " d'un ", " aux ",
            " avec ", " pour ", " être ")


def semble_francais(texte: str) -> bool:
    t = " " + (texte or "").lower().replace("\u2019", "'") + " "
    return sum(t.count(s) for s in _STOP_FR) >= 2


def main() -> None:
    dry = "--dry" in sys.argv
    polluees = "--polluees" in sys.argv
    langs = [a for a in sys.argv[1:] if not a.startswith("-")]

    con = sqlite3.connect(DB, timeout=30)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT cle, texte_fr, lang, traduction "
                       "FROM trad_cache").fetchall()
    print(f"cache : {len(rows)} entrees au total")

    a_supprimer = []
    for r in rows:
        if r["lang"] in langs:
            a_supprimer.append((r["cle"], r["lang"], "langue purgee",
                                r["traduction"][:60]))
        elif polluees and r["lang"] != "fr" and (
                semble_francais(r["traduction"])
                or r["traduction"].strip() == (r["texte_fr"] or "").strip()):
            a_supprimer.append((r["cle"], r["lang"], "restee en francais",
                                r["traduction"][:60]))

    if not a_supprimer:
        print("rien a purger."); return

    par_langue: dict = {}
    for _, lg, motif, _ in a_supprimer:
        par_langue[lg] = par_langue.get(lg, 0) + 1
    print(f"{len(a_supprimer)} entree(s) a purger :", dict(sorted(par_langue.items())))
    for _, lg, motif, apercu in a_supprimer[:8]:
        print(f"   [{lg}] ({motif}) {apercu!r}")
    if len(a_supprimer) > 8:
        print(f"   … et {len(a_supprimer) - 8} autres")

    if dry:
        print("\n--dry : rien supprime."); return

    bak = RACINE / "data" / f"trad_cache_bak-{datetime.now():%Y%m%d-%H%M%S}.json"
    bak.write_text(json.dumps([dict(r) for r in rows], ensure_ascii=False),
                   encoding="utf-8")
    con.executemany("DELETE FROM trad_cache WHERE cle=?",
                    [(c,) for c, *_ in a_supprimer])
    con.commit()
    print(f"\npurge faite — sauvegarde : {bak.name}")
    print("Les textes purges seront retraduits a la volee (prompt verrouille).")


if __name__ == "__main__":
    main()
