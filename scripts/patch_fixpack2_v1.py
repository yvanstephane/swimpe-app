#!/usr/bin/env python3
"""
patch_fixpack2_v1.py — Trois corrections vues sur captures UK/anglais.

A. uk_sponsors.py — BALAYER LE JOB BOARD, pas une page :
   PLAFOND 100 -> 500 (10 pages Adzuna de 50). Le filtre sponsors
   s'applique sur l'ensemble ; la pagination de l'UI parcourt ensuite
   toutes les offres retenues. (Compromis : 1er chargement plus lent ->
   d'ou le cache 12 h deja en place cote jobs_api.)

B. devises.py — « taux indicatif » qui restait en francais :
   note() traduisait deja via tr, MAIS DATE_TAUX (« 2026-07 ») et le mot
   restaient parfois francais faute de tr passe par l'appelant. On rend
   note() AUTO-TRADUISANTE : si aucun tr n'est fourni, elle utilise
   traduction.traduire + la langue de session — plus aucun appelant a
   modifier. La mention « taux indicatif » devient une cle traduite.

C. Rappel : la sidebar en francais (« Connectez-vous... ») = cache
   pollue. Ce patch ne la touche pas ; lance la purge :
       python scripts/purger_trad_v1.py --polluees

Idempotent. Sauvegardes .bak. Syntaxe verifiee, restauration si casse.
Usage : python scripts/patch_fixpack2_v1.py [--dry]
"""
from __future__ import annotations

import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DRY = "--dry" in sys.argv
HORO = datetime.now().strftime("%Y%m%d-%H%M%S")
resultats: list[str] = []


def ecrire(p: Path, contenu: str, n: int) -> None:
    if DRY:
        resultats.append(f"~ {p.name} : {n} retouche(s) [DRY-RUN]")
        return
    bak = p.with_suffix(p.suffix + f".bak-{HORO}")
    shutil.copy2(p, bak)
    p.write_text(contenu, encoding="utf-8")
    try:
        ast.parse(contenu)
    except SyntaxError as e:
        shutil.copy2(bak, p)
        resultats.append(f"x {p.name} : syntaxe cassee l.{e.lineno} — restaure")
        return
    resultats.append(f"v {p.name} : {n} retouche(s) ({bak.name})")


# =========================================================================== #
# A. uk_sponsors.py — plafond
# =========================================================================== #
def patch_uk() -> None:
    p = RACINE / "app" / "api" / "sources" / "uk_sponsors.py"
    if not p.exists():
        resultats.append("- uk_sponsors.py absent")
        return
    src = p.read_text(encoding="utf-8")
    if "PLAFOND = 500" in src:
        resultats.append("= uk_sponsors.py : plafond deja a 500")
        return
    a = ("    PLAFOND = 100          # 2 pages Adzuna de 50 : cout constant")
    if a not in src:
        resultats.append("? uk_sponsors.py : ligne PLAFOND introuvable")
        return
    r = ("    PLAFOND = 500          # 10 pages Adzuna : balaye le job board "
         "(patch_fixpack2)")
    # la boucle _adzuna_gb itere (1, 2) en dur -> la generaliser au plafond
    src = src.replace(a, r, 1)
    boucle = "        for page in (1, 2):"
    if boucle in src:
        src = src.replace(
            boucle,
            "        pages = range(1, (limite // 50) + 2)  # patch_fixpack2\n"
            "        for page in pages:", 1)
    ecrire(p, src, 1)


# =========================================================================== #
# B. devises.py — note() auto-traduisante + cle « taux indicatif »
# =========================================================================== #
A_NOTE = '''def note(montant_eur: float, dest_code: str | None, tr=lambda s: s) -> str:
    """Mention de transparence a mettre en petit sous le prix converti."""
    code, _, _ = devise_de(dest_code)
    if code == "EUR":
        return ""
    return (f"≈ {_format_fr(math.ceil(montant_eur))}\\u00a0€ — "
            + tr("taux indicatif") + f" {DATE_TAUX}")'''

R_NOTE = '''def _tr_auto():
    """tr par defaut (patch_fixpack2) : traduit via le cache Ollama dans la
    langue de session. Evite que « taux indicatif » reste en francais quand
    l'appelant n'a pas transmis de tr."""
    try:
        import streamlit as st
        lg = st.session_state.get("lang", "fr")
        if lg == "fr":
            return lambda s: s
        import traduction
        return lambda s: traduction.traduire(s, lg)
    except Exception:
        return lambda s: s


def note(montant_eur: float, dest_code: str | None, tr=None) -> str:
    """Mention de transparence a mettre en petit sous le prix converti.
    tr=None -> traduction automatique dans la langue de session."""
    code, _, _ = devise_de(dest_code)
    if code == "EUR":
        return ""
    if tr is None:
        tr = _tr_auto()
    return (f"≈ {_format_fr(math.ceil(montant_eur))}\\u00a0€ — "
            + tr("taux indicatif") + f" {tr(DATE_TAUX)}")'''


def patch_devises() -> None:
    p = RACINE / "app" / "api" / "devises.py"
    if not p.exists():
        resultats.append("- devises.py absent")
        return
    src = p.read_text(encoding="utf-8")
    if "_tr_auto" in src:
        resultats.append("= devises.py : note() deja auto-traduisante")
        return
    if A_NOTE not in src:
        resultats.append("? devises.py : fonction note() introuvable a l'identique")
        return
    ecrire(p, src.replace(A_NOTE, R_NOTE, 1), 1)


def main() -> None:
    if DRY:
        print(">>> DRY-RUN\n")
    patch_uk()
    patch_devises()
    print()
    for r in resultats:
        print(" ", r)
    if any(r.startswith("x") for r in resultats):
        sys.exit(1)
    if any(r.startswith("?") for r in resultats):
        sys.exit(2)
    print("\nFINI. Purge le cache pollue, vide le cache offres, relance :")
    print("  python scripts/purger_trad_v1.py --polluees")
    print("  python -c \"import sqlite3;sqlite3.connect('data/mobilite.db',"
          "timeout=30).execute('DELETE FROM jobs_cache').connection.commit()\"")
    print("  pkill -f streamlit ; streamlit run app/api/ui.py")


if __name__ == "__main__":
    main()
