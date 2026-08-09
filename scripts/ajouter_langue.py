#!/usr/bin/env python3
"""
ajouter_langue.py — Ajoute une langue au selecteur, sans risque.

    python scripts/ajouter_langue.py it "🇮🇹 Italiano"
    python scripts/ajouter_langue.py tr "🇹🇷 Türkçe"

Grace au repli universel de i18n.py (toute cle non traduite retombe sur le
francais) et aux surcouches JSON, ajouter une langue ne peut plus faire
planter l'application. Ce script :
  1. insere le code dans LANGUES (idempotent, sauvegarde .bak,
     syntaxe verifiee) ;
  2. imprime les trois commandes de traduction a lancer ensuite
     (interface via Ollama, noms de pays via CLDR, contenus).
"""
from __future__ import annotations

import ast
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
P = RACINE / "app" / "api" / "i18n.py"


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    code = sys.argv[1].strip().lower()
    nom = sys.argv[2].strip()
    if not re.fullmatch(r"[a-z]{2,3}", code):
        print(f"code langue invalide : {code!r} (attendu : it, tr, wo...)")
        sys.exit(1)

    src = P.read_text(encoding="utf-8")
    if re.search(rf'["\']{code}["\']\s*:', src.split("LANGUES", 1)[-1][:600]):
        print(f"= i18n.py : '{code}' deja dans LANGUES")
    else:
        m = re.search(r"LANGUES\s*=\s*\{", src)
        if not m:
            print("? dict LANGUES introuvable — rien ecrit")
            sys.exit(2)
        nouveau = src[:m.end()] + f'\n "{code}": "{nom}",' + src[m.end():]
        ast.parse(nouveau)
        bak = P.with_suffix(f".py.bak-{datetime.now():%Y%m%d-%H%M%S}")
        shutil.copy2(P, bak)
        P.write_text(nouveau, encoding="utf-8")
        print(f"v i18n.py : '{code}': \"{nom}\" ajoute ({bak.name})")

    print("\nEnsuite, les traductions (chacune reprend ou elle s'est arretee) :")
    print(f"  caffeinate -i python scripts/traduire_i18n.py {code} "
          "--modele llama3.3:70b-instruct-q4_K_M")
    print(f"  python scripts/traduire_pays.py {code}")
    print(f"  caffeinate -i python scripts/pretraduire_v3.py {code}")
    print("\nPuis : pkill -f streamlit ; streamlit run app/api/ui.py")


if __name__ == "__main__":
    main()
